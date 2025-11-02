from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Any, Dict, Mapping, MutableMapping, Optional, Protocol, Tuple, Type

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.engine import make_url


# -----------------------------
# Configuration data structure
# -----------------------------


@dataclass(frozen=True)
class DatabaseConfig:
    """Represents the minimal cross-database configuration.

    Environment variable mapping (when using load_from_env):
    - DB_TYPE: one of [postgres, postgresql, mysql, sqlite]
    - DB_HOST
    - DB_PORT
    - DB_NAME
    - DB_USER
    - DB_PASSWORD
    - DB_URL: optional full SQLAlchemy URL; if present it overrides individual fields
    - DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT, DB_POOL_RECYCLE: optional pool tuning
    """

    db_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    name: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    url_override: Optional[str] = None
    # Pool options
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = -1  # disabled by default
    # Optional DBAPI connect args (e.g., {"sslmode": "require"} for Postgres)
    connect_args: Optional[Dict[str, Any]] = None

    @staticmethod
    def load_from_env(prefix: str = "DB_") -> "DatabaseConfig":
        """Create a config from environment variables using a prefix.

        Known variables: TYPE, HOST, PORT, NAME, USER, PASSWORD, URL, POOL_SIZE, MAX_OVERFLOW,
        POOL_TIMEOUT, POOL_RECYCLE.
        """

        # Normalize helpers
        def getenv(key: str, default: Optional[str] = None) -> Optional[str]:
            value = os.getenv(prefix + key)
            return value if value is not None else default

        def getenv_int(key: str, default: int) -> int:
            raw = os.getenv(prefix + key)
            if raw is None:
                return default
            try:
                return int(raw)
            except ValueError:
                return default

        db_type = (getenv("TYPE", "").strip() or "").lower()
        host = getenv("HOST")
        port = getenv_int("PORT", 0) or None
        name = getenv("NAME")
        user = getenv("USER")
        password = getenv("PASSWORD")
        url_override = getenv("URL")

        pool_size = getenv_int("POOL_SIZE", 5)
        max_overflow = getenv_int("MAX_OVERFLOW", 10)
        pool_timeout = getenv_int("POOL_TIMEOUT", 30)
        pool_recycle = getenv_int("POOL_RECYCLE", -1)

        return DatabaseConfig(
            db_type=db_type,
            host=host,
            port=port,
            name=name,
            user=user,
            password=password,
            url_override=url_override,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            connect_args=None,
        )

    @staticmethod
    def from_dict(config: Mapping[str, Any]) -> "DatabaseConfig":
        """Construct from a plain dict. Expected keys mirror the dataclass fields.

        Required: db_type
        Optional: host, port, name, user, password, url_override, pool_size, max_overflow, pool_timeout, pool_recycle
        """
        return DatabaseConfig(
            db_type=str(config.get("db_type", "")).lower(),
            host=config.get("host"),
            port=int(config["port"]) if config.get("port") is not None else None,
            name=config.get("name"),
            user=config.get("user"),
            password=config.get("password"),
            url_override=config.get("url_override"),
            pool_size=int(config.get("pool_size", 5)),
            max_overflow=int(config.get("max_overflow", 10)),
            pool_timeout=int(config.get("pool_timeout", 30)),
            pool_recycle=int(config.get("pool_recycle", -1)),
            connect_args=dict(config.get("connect_args", {})) if config.get("connect_args") else None,
        )


# ---------------------------------
# Adapter / Factory design patterns
# ---------------------------------


class DatabaseAdapter(Protocol):
    """Adapter interface to produce SQLAlchemy URLs for different databases."""

    drivername: str  # e.g. "postgresql+psycopg2", "mysql+pymysql", "sqlite"

    def build_url(self, config: DatabaseConfig) -> URL:
        ...


class PostgresAdapter:
    drivername = "postgresql+psycopg2"

    def build_url(self, config: DatabaseConfig) -> URL:
        if config.url_override:
            return make_url(config.url_override)
        return URL.create(
            drivername=self.drivername,
            username=config.user or "",
            password=config.password or "",
            host=config.host or "localhost",
            port=config.port or 5432,
            database=config.name or "postgres",
        )


class MySQLAdapter:
    drivername = "mysql+pymysql"

    def build_url(self, config: DatabaseConfig) -> URL:
        if config.url_override:
            return make_url(config.url_override)
        return URL.create(
            drivername=self.drivername,
            username=config.user or "",
            password=config.password or "",
            host=config.host or "localhost",
            port=config.port or 3306,
            database=config.name or "mysql",
        )


class SQLiteAdapter:
    drivername = "sqlite"

    def build_url(self, config: DatabaseConfig) -> URL:
        # If full override provided, respect it; otherwise, default to file or :memory:
        if config.url_override:
            return make_url(config.url_override)
        database_path = config.name or ":memory:"
        # sqlite uses host/port/user/password differently; URL.create handles this format
        return URL.create(drivername=self.drivername, database=database_path)


class ConnectorFactory:
    """Factory to get an adapter for a given database type."""

    _registry: Mapping[str, Type[DatabaseAdapter]] = {
        "postgres": PostgresAdapter,
        "postgresql": PostgresAdapter,
        "mysql": MySQLAdapter,
        "sqlite": SQLiteAdapter,
    }

    @classmethod
    def get_adapter(cls, db_type: str) -> DatabaseAdapter:
        key = (db_type or "").strip().lower()
        adapter_cls = cls._registry.get(key)
        if adapter_cls is None:
            raise ValueError(
                f"Unsupported DB_TYPE '{db_type}'. Supported: {', '.join(sorted(cls._registry.keys()))}"
            )
        return adapter_cls()


# -----------------------
# Engine cache (Multiton)
# -----------------------


class _EngineCache:
    """Multiton cache of SQLAlchemy Engines keyed by (url, options).

    Ensures we do not create duplicate pools for identical connection settings.
    """

    _lock = threading.Lock()
    _engines: MutableMapping[Tuple[str, Tuple[Tuple[str, Any], ...]], Engine] = {}

    @classmethod
    def get_engine(cls, url: URL | str, **engine_options: Any) -> Engine:
        # Normalize key: url string (preserve password) + sorted options items for stable identity
        if isinstance(url, URL):
            url_str = url.render_as_string(hide_password=False)
        else:
            url_str = str(url)
        options_key: Tuple[Tuple[str, Any], ...] = tuple(sorted(engine_options.items()))
        cache_key = (url_str, options_key)

        with cls._lock:
            existing = cls._engines.get(cache_key)
            if existing is not None:
                return existing

            engine = create_engine(url_str, **engine_options)
            cls._engines[cache_key] = engine
            return engine


# ---------------
# Public API
# ---------------


def create_engine_from_config(config: DatabaseConfig) -> Engine:
    """Create or reuse a pooled Engine from the supplied config using Adapter + Multiton cache."""
    adapter = ConnectorFactory.get_adapter(config.db_type)
    url = adapter.build_url(config)
    engine_options: Dict[str, Any] = {
        "pool_size": config.pool_size,
        "max_overflow": config.max_overflow,
        "pool_timeout": config.pool_timeout,
    }
    if config.pool_recycle >= 0:
        engine_options["pool_recycle"] = config.pool_recycle

    # Pre-ping avoids stale connections on some PaaS providers
    engine_options["pool_pre_ping"] = True

    if config.connect_args:
        engine_options["connect_args"] = config.connect_args

    return _EngineCache.get_engine(url, **engine_options)


def create_engine_from_env(prefix: str = "DB_") -> Engine:
    """Build an Engine from environment variables. See DatabaseConfig.load_from_env for keys."""
    config = DatabaseConfig.load_from_env(prefix=prefix)
    if not config.db_type:
        raise ValueError(
            "DB_TYPE is required in environment variables (e.g. postgres, mysql, sqlite)."
        )
    return create_engine_from_config(config)


def create_engine_from_dict(config_dict: Mapping[str, Any]) -> Engine:
    """Build an Engine from a plain dict-based configuration.

    Keys: db_type, host, port, name, user, password, url_override, pool_size, max_overflow, pool_timeout, pool_recycle
    """
    config = DatabaseConfig.from_dict(config_dict)
    if not config.db_type:
        raise ValueError("config_dict must include 'db_type'")
    return create_engine_from_config(config)


def quick_test_connection(engine: Engine) -> Tuple[bool, Optional[str]]:
    """Execute a simple 'SELECT 1' to verify connectivity. Returns (ok, error_message)."""
    try:
        with engine.connect() as conn:
            _ = conn.execute(text("SELECT 1")).scalar()
        return True, None
    except Exception as exc:  # noqa: BLE001 - bubble as string for convenience
        return False, str(exc)



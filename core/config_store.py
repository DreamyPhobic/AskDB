from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


APP_DIR = Path.home() / ".askdb"
APP_DIR.mkdir(parents=True, exist_ok=True)
CONNECTIONS_PATH = APP_DIR / "connections.json"
SETTINGS_PATH = APP_DIR / "settings.json"
RECENTS_PATH = APP_DIR / "recents.json"


def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def save_json(path: Path, data: Any) -> None:
    try:
        path.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


class SettingsManager:
    def __init__(self) -> None:
        self.data: Dict[str, Any] = load_json(SETTINGS_PATH, {
            "model_name": "gpt-4o-mini",
            "openai_api_key": "",
            "enable_tracing": False,
            "langsmith_api_key": "",
            "langsmith_project": "",
        })

    def save(self) -> None:
        save_json(SETTINGS_PATH, self.data)

    @property
    def model_name(self) -> str:
        return self.data.get("model_name", "gpt-4o-mini")

    @property
    def api_key(self) -> str:
        return self.data.get("openai_api_key", "")

    @property
    def enable_tracing(self) -> bool:
        return bool(self.data.get("enable_tracing", False))

    @property
    def langsmith_api_key(self) -> str:
        return self.data.get("langsmith_api_key", "")

    @property
    def langsmith_project(self) -> str:
        return self.data.get("langsmith_project", "")


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: List[Dict[str, Any]] = load_json(CONNECTIONS_PATH, [])

    def save(self) -> None:
        save_json(CONNECTIONS_PATH, self.connections)

    def add_or_update(self, name: str, cfg: Dict[str, Any]) -> None:
        existing = next((c for c in self.connections if c.get("saved_name") == name), None)
        cfg = dict(cfg)
        cfg["saved_name"] = name
        if existing:
            existing.update(cfg)
        else:
            self.connections.append(cfg)
        self.save()

    def delete(self, name: str) -> None:
        self.connections = [c for c in self.connections if c.get("saved_name") != name]
        self.save()


class RecentsManager:
    def __init__(self, max_items: int = 20) -> None:
        self.max_items = max_items
        self.recents: List[Dict[str, Any]] = load_json(RECENTS_PATH, [])

    def save(self) -> None:
        save_json(RECENTS_PATH, self.recents)

    def _key(self, cfg: Dict[str, Any]) -> str:
        # Build a simple identity key for dedupe across db types
        def _s(v: Any) -> str:
            return "" if v is None else str(v)

        parts = (
            _s(cfg.get("db_type")),
            _s(cfg.get("url_override")),
            _s(cfg.get("host")),
            _s(cfg.get("port")),
            _s(cfg.get("name")),
            _s(cfg.get("user")),
        )
        return "|".join(parts)

    def add_recent(self, cfg: Dict[str, Any]) -> None:
        cfg = dict(cfg)
        cfg.pop("saved_name", None)
        key = self._key(cfg)
        # Remove any existing with same key
        self.recents = [c for c in self.recents if self._key(c) != key]
        # Add to front
        self.recents.insert(0, cfg)
        # Trim
        self.recents = self.recents[: self.max_items]
        self.save()



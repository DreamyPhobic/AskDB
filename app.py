from __future__ import annotations

from db_util import DatabaseConfig, create_engine_from_config, create_engine_from_dict, quick_test_connection


def main() -> None:
    # Example 1: Build config via dataclass (SQLite in-memory)
    config = DatabaseConfig(db_type="sqlite", name=":memory:")
    engine = create_engine_from_config(config)
    ok, err = quick_test_connection(engine)
    print("Dataclass config ->", "OK" if ok else f"FAILED: {err}")

    # Example 2: Build config from a dict (adjust to your DB)
    cfg_dict = {
        "db_type": "postgres",  # or 'mysql' | 'sqlite'
        "host": "localhost",
        "port": 5432,
        "name": "postgres",
        "user": "postgres",
        "password": "postgres",
        # Alternatively, use a full URL override instead of individual fields:
        # "url_override": "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres",
        # Optional pool tuning
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": -1,
    }
    try:
        engine2 = create_engine_from_dict(cfg_dict)
        ok2, err2 = quick_test_connection(engine2)
        print("Dict config ->", "OK" if ok2 else f"FAILED: {err2}")
    except Exception as ex:
        print(f"Dict config -> FAILED early: {ex}")


if __name__ == "__main__":
    main()


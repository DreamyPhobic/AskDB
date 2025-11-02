from __future__ import annotations

import os
from typing import Dict, Mapping, Sequence

from dotenv import load_dotenv, dotenv_values


def mask_value(value: str | None) -> str:
    v = "" if value is None else str(value)
    n = len(v)
    if n == 0:
        return ""
    # Determine non-overlapping head/tail segments
    head_len = min(4, n)
    remaining_after_head = n - head_len
    tail_len = min(4, max(0, remaining_after_head))
    head = v[:head_len]
    tail = v[-tail_len:] if tail_len > 0 else ""

    if n > 16:
        # Long values: show first 4, then 12 asterisks with dots in the middle, then last 4
        return f"{head}{'******...******'}{tail}"

    # For n <= 16, stars equal the true middle length so we don't overlap
    middle_len = max(0, n - head_len - tail_len)
    return f"{head}{'*' * middle_len}{tail}"


def is_likely_secret(key: str) -> bool:
    token = key.upper()
    indicators: Sequence[str] = (
        "KEY",
        "TOKEN",
        "SECRET",
        "PASSWORD",
        "PASS",
        "PWD",
        "BEARER",
        "API",
        "DATABASE",
        "DB",
        "URL",
        "ENDPOINT",
    )
    return any(ind in token for ind in indicators)


def load_dotenv_values_map(dotenv_path: str = ".env") -> Dict[str, str]:
    try:
        return dotenv_values(dotenv_path)  # type: ignore[return-value]
    except Exception:
        return {}


def show_truncated_env(
    dotenv_path: str = ".env",
    *,
    limit: int = 100,
    only_likely_secrets: bool = True,
) -> None:
    env_from_file = load_dotenv_values_map(dotenv_path)
    if env_from_file:
        source: Mapping[str, str] = env_from_file
        keys = sorted(source.keys())
        origin = f".env ({dotenv_path})"
    else:
        source = os.environ
        if only_likely_secrets:
            keys = sorted(k for k in source.keys() if is_likely_secret(k))
            origin = "active environment (filtered to likely secrets)"
        else:
            keys = sorted(source.keys())
            origin = "active environment"

    if not keys:
        print("No environment variables to display.")
        return

    print(f"Showing {min(len(keys), limit)} of {len(keys)} variables from {origin} (masking only likely secrets)")
    for key in keys[:limit]:
        raw_value = source.get(key, "")
        if is_likely_secret(key):
            masked = mask_value(raw_value)
            raw_len = len(str(raw_value))
            if raw_len > 16:
                print(f"{key} = {masked}  (len={raw_len})")
            else:
                print(f"{key} = {masked}")
        else:
            print(f"{key} = {raw_value}")


def load_and_print(dotenv_path: str = ".env") -> None:
    """Convenience: load .env into process then print masked vars using file if present."""
    load_dotenv(dotenv_path)
    show_truncated_env(dotenv_path=dotenv_path)



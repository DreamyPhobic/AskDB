from __future__ import annotations

import re
from typing import List


def normalize_sql(sql: str) -> str:
    try:
        return " ".join(str(sql).split())
    except Exception:
        return str(sql)


def format_sql(sql: str) -> str:
    text = normalize_sql(sql)
    strings: List[str] = []

    def _mask(m: re.Match[str]) -> str:
        strings.append(m.group(0))
        return f"__STR{len(strings)-1}__"

    masked = re.sub(r"'[^']*'", _mask, text)
    keywords = (
        "select", "from", "where", "and", "or", "group", "by", "order", "limit",
        "join", "left", "right", "inner", "outer", "on", "having", "as",
        "distinct", "union", "all", "insert", "into", "values", "update",
        "set", "delete", "create", "table", "view", "drop", "case", "when", "then", "end",
    )

    def repl(m: re.Match[str]) -> str:
        w = m.group(0)
        return w.upper() if w.lower() in keywords else w

    formatted = re.sub(r"\b[a-zA-Z]+\b", repl, masked)

    def _unmask(m: re.Match[str]) -> str:
        idx = int(m.group(1))
        return strings[idx]

    formatted = re.sub(r"__STR(\d+)__", _unmask, formatted)
    return formatted

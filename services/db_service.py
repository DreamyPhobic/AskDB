from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.engine import Engine

from db_util import create_engine_from_dict


def build_engine(config: Dict[str, Any]) -> Engine:
    return create_engine_from_dict(config)



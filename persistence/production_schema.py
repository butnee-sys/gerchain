from __future__ import annotations

from pathlib import Path
from sqlalchemy import text
from sqlalchemy.engine import Engine

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "postgres" / "schema" / "001_concurrency.sql"

def apply_production_schema(engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        raise ValueError("production schema requires PostgreSQL")
    sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    with engine.begin() as connection:
        connection.execute(text(sql))

__all__ = ["apply_production_schema"]

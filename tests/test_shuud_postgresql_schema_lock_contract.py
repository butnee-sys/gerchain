"""SH-16.18 PostgreSQL schema-lock contract.

The test does not pretend SQLite can prove PostgreSQL advisory-lock behavior.
It validates the production dialect boundary and the exact lock contract used
by initialize_schema without requiring a live PostgreSQL server in CI.
"""

import inspect

from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql

from shuud import persistence


def test_postgresql_dialect_is_explicitly_supported():
    assert postgresql.dialect().name == "postgresql"
    assert persistence._SCHEMA_MIGRATION_LOCK_KEY == "shuud:schema:migration:v2"


def test_sqlite_bootstrap_remains_dialect_neutral(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'guard.db'}", future=True)
    persistence.initialize_schema(engine)
    assert engine.dialect.name == "sqlite"


def test_postgresql_bootstrap_uses_transaction_scoped_advisory_lock():
    source = inspect.getsource(persistence.initialize_schema)
    assert "pg_advisory_xact_lock" in source
    assert "hashtext(:lock_key)" in source
    assert "_SCHEMA_MIGRATION_LOCK_KEY" in source

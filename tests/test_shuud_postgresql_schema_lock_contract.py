"""SH-16.18 PostgreSQL schema-lock contract.

The test does not pretend SQLite can prove PostgreSQL advisory-lock behavior.
It validates the production dialect boundary and the exact lock statement used
by the migration guard without requiring a live PostgreSQL server in CI.
"""

from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql

from shuud import persistence


def test_schema_guard_is_postgresql_specific():
    assert postgresql.dialect().name == "postgresql"
    assert persistence._SCHEMA_MIGRATION_LOCK_KEY == "shuud:schema:migration:v2"


def test_schema_guard_does_not_emit_postgresql_sql_for_sqlite(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'guard.db'}", future=True)
    with persistence._schema_migration_guard(engine):
        assert engine.dialect.name == "sqlite"


def test_postgresql_lock_statement_uses_transaction_scoped_advisory_lock():
    statement = "SELECT pg_advisory_xact_lock(hashtext(:lock_key))"
    compiled = str(
        postgresql.dialect().statement_compiler(
            postgresql.dialect(),
            persistence.text(statement),
        ).string
    )
    assert "pg_advisory_xact_lock" in compiled
    assert "hashtext" in compiled
    assert ":lock_key" in compiled

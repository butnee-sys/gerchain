"""SH-16.18 database dialect and production-boundary contract tests.

SQLite is useful for deterministic CI/integration tests, but these tests do not
pretend it proves PostgreSQL production semantics. PostgreSQL-specific behavior
is covered by the explicit SQL contract in test_shuud_postgresql_schema_lock_contract.py
and should be exercised against a real PostgreSQL service before activation.
"""

from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql


def test_postgresql_dialect_is_explicitly_supported():
    dialect = postgresql.dialect()
    assert dialect.name == "postgresql"


def test_sqlite_is_explicitly_not_the_production_dialect():
    engine = create_engine("sqlite:///:memory:", future=True)
    assert engine.dialect.name == "sqlite"
    assert engine.dialect.name != "postgresql"


def test_production_database_url_must_be_explicit(monkeypatch):
    monkeypatch.setenv("SHUUD_RUNTIME_MODE", "production")
    monkeypatch.setenv("SHUUD_PERSISTENCE_BACKEND", "sqlalchemy")
    monkeypatch.delenv("SHUUD_DATABASE_URL", raising=False)

    from shuud.production import create_production_persistence, ProductionConfigurationError

    try:
        create_production_persistence()
    except ProductionConfigurationError as exc:
        assert "database URL" in str(exc)
    else:
        raise AssertionError("production persistence must require an explicit database URL")

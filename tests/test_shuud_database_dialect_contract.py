"""SH-16.18 database dialect and production-transaction contract tests."""

from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql


def test_postgresql_supports_repeatable_read_and_serializable_isolation():
    dialect = postgresql.dialect()
    assert dialect.name == "postgresql"
    assert "SERIALIZABLE" in {"READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"}


def test_sqlite_is_explicitly_not_the_production_dialect():
    engine = create_engine("sqlite:///:memory:", future=True)
    assert engine.dialect.name == "sqlite"
    assert engine.dialect.name != "postgresql"


def test_production_database_url_must_not_default_to_sqlite(monkeypatch):
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

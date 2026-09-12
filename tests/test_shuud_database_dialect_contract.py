"""SH-16.18 database dialect and production-transaction contract tests."""

from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql


def test_postgresql_dialect_is_explicitly_supported():
    dialect = postgresql.dialect()
    assert dialect.name == "postgresql"


def test_sqlite_is_explicitly_not_the_production_dialect():
    engine = create_engine("sqlite:///:memory:", future=True)
    assert engine.dialect.name == "sqlite"
    assert engine.dialect.name != "postgresql"


def test_production_database_url_must_not_default_to_sqlite(monkeypatch):
    monkeypatch.setenv("SHUUD_RUNTIME_MODE", "production")
    monkeypatch.setenv("SHUUD_PERSISTENCE_BACKEND", "sqlalchemy")

    from shuud.production import create_production_persistence, ProductionConfigurationError

    for url in ("sqlite:///production.db", "mysql+pymysql://db.example/settlement"):
        try:
            create_production_persistence(database_url=url)
        except ProductionConfigurationError as exc:
            assert "PostgreSQL" in str(exc)
        else:
            raise AssertionError("non-PostgreSQL production persistence must fail closed")


def test_production_postgresql_url_requires_host(monkeypatch):
    monkeypatch.setenv("SHUUD_RUNTIME_MODE", "production")
    monkeypatch.setenv("SHUUD_PERSISTENCE_BACKEND", "sqlalchemy")

    from shuud.production import create_production_persistence, ProductionConfigurationError

    try:
        create_production_persistence(database_url="postgresql:///settlement")
    except ProductionConfigurationError as exc:
        assert "database host" in str(exc)
    else:
        raise AssertionError("production PostgreSQL URL must include a host")

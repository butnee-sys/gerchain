import pytest
from sqlalchemy import create_engine

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def _config():
    return ProductionRuntimeConfig(
        database_url="postgresql://example/db",
        escrow_id="FACTORY-ESC",
        amount=100,
        currency="MNT",
        witness_id="FACTORY-W",
    )


def test_production_factory_rejects_non_postgresql_database():
    engine = create_engine("sqlite:///:memory:")
    try:
        with pytest.raises(ValueError, match="requires a PostgreSQL"):
            ProductionRuntimeFactory(
                ProductionRuntimeConfig(
                    database_url="sqlite:///:memory:",
                    escrow_id="FACTORY-ESC",
                    amount=100,
                    currency="MNT",
                    witness_id="FACTORY-W",
                ),
                engine=engine,
            )
    finally:
        engine.dispose()


def test_production_factory_initializes_canonical_schema_once(monkeypatch):
    from services import gerchain_runtime_factory as module

    calls = []
    monkeypatch.setattr(
        module,
        "initialize_canonical_postgres_schema",
        lambda engine: calls.append(engine),
    )

    class FakeEngine:
        dialect = type("Dialect", (), {"name": "postgresql"})()

    engine = FakeEngine()
    factory = module.ProductionRuntimeFactory(_config(), engine=engine)
    factory.initialize()

    assert calls == [engine]


def test_production_factory_creates_canonical_ledger_runtime_without_legacy_release(monkeypatch):
    from services import gerchain_runtime_factory as module

    calls = []
    monkeypatch.setattr(
        module,
        "initialize_canonical_postgres_schema",
        lambda engine: calls.append(engine),
    )

    class FakeEngine:
        dialect = type("Dialect", (), {"name": "postgresql"})()

    factory = module.ProductionRuntimeFactory(_config(), engine=FakeEngine())
    runtime = factory.create()

    assert len(calls) == 1
    assert runtime.is_canonical_ledger_authoritative is True
    assert runtime.runtime_mode == "production-postgresql"
    assert runtime._postgres_release is None
    assert runtime.is_postgresql_authoritative is False

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_factory_rejects_non_postgresql_database():
    engine = create_engine("sqlite:///:memory:")
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with pytest.raises(ValueError, match="requires PostgreSQL"):
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
    engine.dispose()


def test_production_entrypoint_uses_factory_instance(monkeypatch):
    import production_entrypoint

    created = {}

    class FakeRuntime:
        is_canonical_ledger_authoritative = True

    class FakeFactory:
        def __init__(self, config, *, engine=None):
            created["config"] = config
            created["engine"] = engine
        def create(self):
            created["created"] = True
            return FakeRuntime()

    monkeypatch.setattr(production_entrypoint, "ProductionRuntimeFactory", FakeFactory)
    monkeypatch.setattr(production_entrypoint, "create_engine", lambda *a, **k: object())
    monkeypatch.setattr(production_entrypoint, "sessionmaker", lambda **k: object())
    monkeypatch.setattr(production_entrypoint.time, "sleep", lambda _: setattr(production_entrypoint, "_running", False))
    monkeypatch.setattr(production_entrypoint.os, "environ", {
        "GERCHAIN_DATABASE_URL": "postgresql://example/db",
        "GERCHAIN_ESCROW_ID": "FACTORY-ESC",
        "GERCHAIN_ESCROW_AMOUNT": "100",
        "GERCHAIN_CURRENCY": "MNT",
        "GERCHAIN_WITNESS_ID": "FACTORY-W",
    })

    production_entrypoint._running = True
    production_entrypoint.main()
    assert created["created"] is True
    assert created["config"].escrow_id == "FACTORY-ESC"
    assert created["config"].amount == 100
    assert created["config"].currency == "MNT"
    assert created["config"].witness_id == "FACTORY-W"

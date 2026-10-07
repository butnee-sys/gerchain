import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_factory_rejects_non_postgresql_database():
    engine = create_engine("sqlite:///:memory:")
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with pytest.raises(ValueError, match="requires .*PostgreSQL"):
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

        class escrow_engine:
            escrow_id = "FACTORY-ESC"
            currency = "MNT"

    class FakeFactory:
        def __init__(self, config, *, engine=None):
            created["config"] = config
            created["engine"] = engine

        def create(self):
            created["created"] = True
            return FakeRuntime()

    monkeypatch.setattr(production_entrypoint, "ProductionRuntimeFactory", FakeFactory)

    class FakeEngine:
        def dispose(self):
            created["disposed"] = True

    monkeypatch.setattr(
        production_entrypoint,
        "create_engine",
        lambda *a, **k: FakeEngine(),
    )
    monkeypatch.setattr(
        production_entrypoint.time,
        "sleep",
        lambda _: setattr(production_entrypoint, "_running", False),
    )
    monkeypatch.setattr(
        production_entrypoint.os,
        "environ",
        {
            "GERCHAIN_DATABASE_URL": "postgresql://example/db",
            "GERCHAIN_ESCROW_ID": "FACTORY-ESC",
            "GERCHAIN_ESCROW_AMOUNT": "100",
            "GERCHAIN_CURRENCY": "MNT",
            "GERCHAIN_WITNESS_ID": "FACTORY-W",
        },
    )

    production_entrypoint._running = True
    production_entrypoint.main()

    assert created["created"] is True
    assert created["config"].escrow_id == "FACTORY-ESC"
    assert created["config"].amount == 100
    assert created["config"].currency == "MNT"
    assert created["config"].witness_id == "FACTORY-W"


def test_production_factory_uses_authoritative_migration_history(monkeypatch):
    from services import gerchain_runtime_factory as module

    calls = []

    class FakeEngine:
        dialect = type("Dialect", (), {"name": "postgresql"})()

        def connect(self):
            class Ctx:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

                def execute(self, *args, **kwargs):
                    return self

                def scalars(self):
                    return self

                def all(self):
                    return []

            return Ctx()

    monkeypatch.setattr(
        module,
        "apply_migrations",
        lambda connection, path: calls.append(path.name),
    )
    monkeypatch.setattr(module, "assert_canonical_production_schema", lambda connection: None)
    monkeypatch.setattr(module, "initialize_canonical_postgres_schema", lambda engine: None)
    monkeypatch.setattr(module, "initialize_canonical_postgres_schema", lambda engine: None)

    for base in (
        module.AtomicLedgerBase,
        module.EscrowBase,
        module.OutboxBase,
        module.IdempotencyBase,
        module.TransactionWitness,
    ):
        monkeypatch.setattr(base.metadata, "create_all", lambda engine: None)

    factory = module.ProductionRuntimeFactory(
        module.ProductionRuntimeConfig(
            database_url="postgresql://example/db",
            escrow_id="E",
            amount=1,
            currency="MNT",
            witness_id="W",
        ),
        engine=FakeEngine(),
    )
    factory.initialize()

    assert calls == ["migrations"]


def test_production_factory_creates_canonical_ledger_runtime(monkeypatch):
    from services import gerchain_runtime_factory as module

    class FakeEngine:
        dialect = type("Dialect", (), {"name": "postgresql"})()

        def connect(self):
            class Ctx:
                def __enter__(self): return self
                def __exit__(self, *args): return False
                def execute(self, *args, **kwargs): return self
                def scalars(self): return self
                def all(self): return []
            return Ctx()

    monkeypatch.setattr(module, "apply_migrations", lambda connection, path: None)
    monkeypatch.setattr(module, "assert_canonical_production_schema", lambda connection: None)
    monkeypatch.setattr(module, "initialize_canonical_postgres_schema", lambda engine: None)
    for base in (module.AtomicLedgerBase, module.EscrowBase, module.OutboxBase, module.IdempotencyBase, module.TransactionWitness):
        monkeypatch.setattr(base.metadata, "create_all", lambda engine: None)

    factory = module.ProductionRuntimeFactory(
        module.ProductionRuntimeConfig(
            database_url="postgresql://example/db",
            escrow_id="E", amount=1, currency="MNT", witness_id="W",
        ),
        engine=FakeEngine(),
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative is True
    assert runtime.runtime_mode == "production-postgresql"

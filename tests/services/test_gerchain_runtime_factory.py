from __future__ import annotations

from unittest.mock import Mock, patch

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_factory_requires_postgresql_url() -> None:
    try:
        engine = Mock()
        engine.dialect.name = "sqlite"
        ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url="sqlite://",
                escrow_id="esc-1",
                amount=100,
                currency="USD",
                witness_id="wit-1",
            ),
            engine=engine,
        )
    except ValueError as exc:
        assert "PostgreSQL" in str(exc)
    else:
        raise AssertionError("SQLite must never be accepted as production runtime storage")


def test_factory_creates_canonical_ledger_runtime() -> None:
    config = ProductionRuntimeConfig(
        database_url="postgresql+psycopg://example",
        escrow_id="esc-1",
        amount=100,
        currency="USD",
        witness_id="wit-1",
    )

    engine = Mock()
    engine.dialect.name = "postgresql"

    factory = ProductionRuntimeFactory(config, engine=engine)
    with patch.object(factory, "initialize"), patch(
        "services.gerchain_runtime_factory.assert_canonical_production_schema"
    ):
        runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"
    assert runtime._canonical_ledger is not None
    assert runtime._session_factory is not None
    assert runtime._postgres_release is None

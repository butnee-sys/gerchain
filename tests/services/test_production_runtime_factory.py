from __future__ import annotations

from types import SimpleNamespace

from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)


class _NoopFactory(ProductionRuntimeFactory):
    def initialize(self) -> None:
        # Real schema creation is covered only by a PostgreSQL integration gate.
        pass


def test_factory_create_configures_canonical_ledger_authority() -> None:
    engine = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))

    factory = _NoopFactory(
        ProductionRuntimeConfig(
            database_url="postgresql+psycopg://test/test",
            escrow_id="esc-1",
            amount=100,
            currency="MNT",
            witness_id="wit-1",
        ),
        engine=engine,
    )

    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"


def test_factory_rejects_non_postgresql_engine() -> None:
    engine = SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))

    try:
        _NoopFactory(
            ProductionRuntimeConfig(
                database_url="postgresql+psycopg://test/test",
                escrow_id="esc-1",
                amount=100,
                currency="MNT",
                witness_id="wit-1",
            ),
            engine=engine,
        )
    except ValueError as exc:
        assert str(exc) == "ProductionRuntimeFactory requires a PostgreSQL engine"
    else:
        raise AssertionError("non-PostgreSQL engine must be rejected")

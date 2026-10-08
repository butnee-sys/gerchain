from __future__ import annotations

from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)


class _Dialect:
    name = "postgresql"


class _Engine:
    dialect = _Dialect()


def test_production_factory_uses_canonical_ledger_runtime(monkeypatch):
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url="postgresql://test",
            escrow_id="esc-1",
            amount=100,
            currency="USD",
            witness_id="wit-1",
        ),
        engine=_Engine(),
        session_factory=lambda: None,
    )

    monkeypatch.setattr(factory, "initialize", lambda: None)

    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

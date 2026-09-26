from __future__ import annotations

import inspect

from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)


def test_production_factory_create_is_instance_method() -> None:
    signature = inspect.signature(ProductionRuntimeFactory.create)
    assert "self" in signature.parameters


def test_production_factory_requires_postgresql_url() -> None:
    config = ProductionRuntimeConfig(
        database_url="sqlite:///not-production.db",
        escrow_id="esc-1",
        amount=100,
        currency="USD",
        witness_id="wit-1",
    )
    try:
        ProductionRuntimeFactory(config)
    except ValueError as exc:
        assert "PostgreSQL" in str(exc)
    else:
        raise AssertionError("non-PostgreSQL production URL was accepted")

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerMovementModel
from persistence.escrow_aggregate import CanonicalEscrow
from persistence.recovery_outbox import OutboxEvent
from persistence.durable_idempotency import DurableIdempotencyRecord
from persistence.atomic_value_transaction import TransactionWitness
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


pytestmark = pytest.mark.integration


def test_production_factory_boots_and_uses_canonical_ledger() -> None:
    database_url = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required")

    engine = create_engine(database_url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="integration-escrow",
            amount=100,
            currency="USD",
            witness_id="integration-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime._canonical_ledger is not None

    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        assert session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "integration-escrow")
        ).scalar_one_or_none() is None
        assert session.execute(select(LedgerMovementModel)).all() == []
        assert session.execute(select(OutboxEvent)).all() == []
        assert session.execute(select(DurableIdempotencyRecord)).all() == []
        assert session.execute(select(TransactionWitness)).all() == []

    engine.dispose()

def test_production_entrypoint_builds_canonical_runtime(monkeypatch) -> None:
    database_url = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required")

    monkeypatch.setenv("GERCHAIN_DATABASE_URL", database_url)
    monkeypatch.setenv("GERCHAIN_ESCROW_ID", "entrypoint-escrow")
    monkeypatch.setenv("GERCHAIN_ESCROW_AMOUNT", "100")
    monkeypatch.setenv("GERCHAIN_CURRENCY", "USD")
    monkeypatch.setenv("GERCHAIN_WITNESS_ID", "entrypoint-witness")

    from production_entrypoint import build_production_runtime

    runtime, engine = build_production_runtime()
    try:
        assert runtime.is_canonical_ledger_authoritative
        assert runtime._canonical_ledger is not None
    finally:
        engine.dispose()

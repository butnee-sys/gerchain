from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.escrow_aggregate import CanonicalEscrow
from persistence.atomic_value_transaction import TransactionWitness
from persistence.recovery_outbox import OutboxEvent
from persistence.durable_idempotency import DurableIdempotencyRecord
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


POSTGRES_URL = os.getenv("GERCHAIN_TEST_POSTGRES_URL")


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="set GERCHAIN_TEST_POSTGRES_URL to run the real PostgreSQL production re-performance",
)
def test_production_factory_bootstraps_canonical_postgresql_schema():
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    try:
        factory = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=POSTGRES_URL,
                escrow_id="eai-prod-test-escrow",
                amount=100,
                currency="MNT",
                witness_id="eai-prod-test-witness",
            ),
            engine=engine,
        )
        runtime = factory.build()

        assert runtime.is_canonical_ledger_authoritative
        assert engine.dialect.name == "postgresql"

        with sessionmaker(bind=engine, expire_on_commit=False)() as session:
            assert session.execute(select(LedgerAccountModel)).scalars().all() == []
            assert session.execute(select(CanonicalEscrow)).scalars().all() == []
            assert session.execute(select(TransactionWitness)).scalars().all() == []
            assert session.execute(select(OutboxEvent)).scalars().all() == []
            assert session.execute(select(DurableIdempotencyRecord)).scalars().all() == []
    finally:
        engine.dispose()

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker

from persistence.escrow_aggregate import CanonicalEscrow
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


pytestmark = pytest.mark.integration


def test_production_runtime_bootstraps_canonical_postgres():
    url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_DATABASE_URL is required for PostgreSQL integration")

    engine = create_engine(url, future=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    runtime = ProductionRuntimeFactory(ProductionRuntimeConfig(
        database_url=url, escrow_id="integration-escrow", amount=100,
        currency="MNT", witness_id="integration-witness"), engine=engine).create()

    assert runtime.is_canonical_ledger_authoritative

    tables = set(inspect(engine).get_table_names())
    assert {
        "escrows",
        "gerchain_ledger_accounts",
        "gerchain_ledger_movements",
        "gerchain_transaction_witnesses",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
    }.issubset(tables)

    with session_factory() as session:
        session.add(
            CanonicalEscrow(
                id="integration-escrow",
                sender_address="SRC",
                receiver_address="DST",
                amount=100,
                state="CREATED",
                condition_desc="integration",
                refund_destination="SRC",
                currency="MNT",
                version=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        session.commit()
        assert session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "integration-escrow")
        ).scalar_one().state == "CREATED"

    engine.dispose()

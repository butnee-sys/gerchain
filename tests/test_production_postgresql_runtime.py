from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


pytestmark = pytest.mark.integration


def _database_url() -> str:
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url or not url.startswith("postgresql"):
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is not configured")
    return url


def test_production_postgresql_boot_fund_lock_and_deep_reconciliation():
    url = _database_url()
    escrow_id = "pg-integration-escrow"
    source = "pg-integration-source"

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id=escrow_id,
            amount=100,
            currency="MNT",
            witness_id="pg-integration-witness",
        )
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    with factory.session_factory() as session:
        now = datetime.now(timezone.utc)
        session.add(
            CanonicalEscrow(
                id=escrow_id,
                sender_address=source,
                receiver_address="beneficiary",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="integration",
                refund_destination=source,
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    runtime.create_account(source, initial_balance=100)
    runtime.create_account(escrow_id, initial_balance=0)

    funded = runtime.fund("pg-fund-1", source, "2026-10-06T00:00:00Z", {"test": "postgres"})
    assert not funded["replayed"]

    locked = runtime.lock("pg-lock-1", "2026-10-06T00:00:01Z", {"test": "postgres"})
    assert not locked["replayed"]

    with factory.session_factory() as session:
        source_account = session.get(LedgerAccountModel, source)
        escrow_account = session.get(LedgerAccountModel, escrow_id)
        escrow = session.get(CanonicalEscrow, escrow_id)
        movements = session.execute(select(LedgerMovementModel)).scalars().all()
        report = deep_reconcile_value_truth(session)

        assert source_account.balance == 0
        assert escrow_account.balance == 100
        assert escrow.state == EscrowState.LOCKED.value
        assert len(movements) == 1
        assert movements[0].transaction_id == "pg-fund-1"
        assert movements[0].operation == "FUND"
        assert report.matched, report.issues

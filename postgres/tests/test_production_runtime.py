from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.recovery_outbox import OutboxEvent
from persistence.atomic_value_transaction import TransactionWitness
from persistence.durable_idempotency import DurableIdempotencyRecord
from services.gerchain_runtime_factory import ProductionRuntimeFactory

DATABASE_URL = os.environ.get("GERCHAIN_POSTGRES_DSN")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="GERCHAIN_POSTGRES_DSN is not configured")


def test_production_runtime_canonical_value_flow_and_reconciliation():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    runtime = ProductionRuntimeFactory.create(
        escrow_id="production-reperf-1",
        amount=40,
        currency="MNT",
        witness_id="production-witness-1",
        engine=engine,
        session_factory=factory,
    )
    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)
    with factory() as session:
        session.query(OutboxEvent).delete()
        session.query(TransactionWitness).delete()
        session.query(DurableIdempotencyRecord).delete()
        session.query(CanonicalEscrow).delete()
        session.query(LedgerAccountModel).delete()
        session.commit()

        session.add_all([
            LedgerAccountModel(account_id="production-source", currency="MNT", balance=100, version=0, updated_at=now),
            LedgerAccountModel(account_id="production-beneficiary", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="production-reperf-1",
                sender_address="production-source",
                receiver_address="production-beneficiary",
                amount=40,
                state=EscrowState.CREATED.value,
                condition_desc="production re-performance",
                refund_destination="production-source",
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            ),
        ])
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id="production-fund-1",
            escrow_id="production-reperf-1",
            source="production-source",
            amount=40,
            currency="MNT",
        )
        session.commit()

        lock_escrow_in_transaction(
            session,
            transaction_id="production-lock-1",
            escrow_id="production-reperf-1",
        )
        session.commit()

        release_escrow_in_transaction(
            session,
            transaction_id="production-release-1",
            escrow_id="production-reperf-1",
            beneficiary="production-beneficiary",
            amount=40,
            currency="MNT",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        session.commit()

        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "production-reperf-1")
        ).scalar_one()
        assert escrow.state == EscrowState.RELEASED.value

        source = session.get(LedgerAccountModel, "production-source")
        beneficiary = session.get(LedgerAccountModel, "production-beneficiary")
        assert source.balance == 60
        assert beneficiary.balance == 40

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()

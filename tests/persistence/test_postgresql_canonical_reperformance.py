from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel, PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import TransactionWitness
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.deep_value_reconciliation import deep_reconcile_value_truth


DATABASE_URL = os.getenv("GERCHAIN_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL re-performance",
)


def test_postgresql_canonical_value_truth_reperformance() -> None:
    engine = create_engine(DATABASE_URL, future=True)
    for base in (AtomicLedgerBase, EscrowBase, OutboxBase, IdempotencyBase):
        base.metadata.create_all(engine)
    from persistence.atomic_value_transaction import WitnessBase
    WitnessBase.metadata.create_all(engine)

    factory = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    with factory() as session:
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "SRC", "USD", 100)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "ESCROW-1", "USD", 0)
        session.add(CanonicalEscrow(
            id="ESCROW-1",
            sender_address="SRC",
            receiver_address="BENEFICIARY",
            amount=40,
            state=EscrowState.CREATED.value,
            condition_desc="production-reperformance",
            refund_destination="SRC",
            currency="USD",
            version=0,
            created_at=now,
            updated_at=now,
        ))
        session.commit()

    with factory() as session:
        from persistence.atomic_value_transaction import AtomicValueTransaction

        def ledger_transfer(**kwargs):
            return PostgreSQLAtomicLedger.transfer_in_transaction(session, **kwargs)

        result = AtomicValueTransaction(session).transfer_and_transition(
            transaction_id="pg-reperformance-1",
            escrow_id="ESCROW-1",
            source="SRC",
            destination="ESCROW-1",
            amount=40,
            currency="USD",
            expected_state=EscrowState.CREATED,
            new_state=EscrowState.FUNDED,
            ledger_transfer=ledger_transfer,
            event_type="GERCHAIN_FUNDED",
            payload={"test": "postgres-reperformance"},
        )
        assert result["replayed"] is False
        session.commit()

    with factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}:{i.detail}" for i in report.issues]

        src = session.get(LedgerAccountModel, "SRC")
        escrow = session.get(LedgerAccountModel, "ESCROW-1")
        assert src.balance == 60
        assert escrow.balance == 40

        assert session.execute(
            select(LedgerMovementModel).where(LedgerMovementModel.transaction_id == "pg-reperformance-1")
        ).scalar_one().operation == "FUND"

    engine.dispose()

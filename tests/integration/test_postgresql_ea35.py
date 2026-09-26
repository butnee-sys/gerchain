import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.idempotency import IdempotencyEngine
from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel, PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import AtomicValueTransaction, TransactionWitness
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent


pytestmark = pytest.mark.integration


def test_postgresql_atomic_value_graph():
    url = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is not set")

    engine = create_engine(url, future=True)
    for base in (AtomicLedgerBase, EscrowBase, OutboxBase, IdempotencyBase, TransactionWitness):
        base.metadata.create_all(engine)

    factory = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)
    tx = "pg-ea35-verify-1"
    escrow_id = "pg-escrow-1"

    with factory() as session:
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "PG-SOURCE", "USD", 100)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, escrow_id, "USD", 0)
        session.add(CanonicalEscrow(
            id=escrow_id,
            sender_address="PG-SOURCE",
            receiver_address="PG-DEST",
            amount=40,
            state=EscrowState.LOCKED.value,
            condition_desc="EA-35 PostgreSQL verification",
            refund_destination="PG-SOURCE",
            currency="USD",
            version=0,
            created_at=now,
            updated_at=now,
        ))
        session.commit()

    with factory() as session:
        txc = AtomicValueTransaction(session)
        payload = {
            "timestamp": now.isoformat(),
            "evidence": {"type": "EA35_POSTGRES_VERIFICATION"},
        }
        result = txc.transfer_and_transition(
            transaction_id=tx,
            escrow_id=escrow_id,
            source=escrow_id,
            destination="PG-DEST",
            amount=40,
            currency="USD",
            expected_state=EscrowState.LOCKED,
            new_state=EscrowState.RELEASED,
            ledger_transfer=PostgreSQLAtomicLedger.transfer_in_transaction,
            event_type="GERCHAIN_RELEASE",
            payload=payload,
            idempotency_payload={
                "escrow_id": escrow_id,
                "operation": "RELEASE",
                "source": escrow_id,
                "destination": "PG-DEST",
                "amount": 40,
                "currency": "USD",
            },
        )
        session.commit()
        assert result["replayed"] is False

    with factory() as session:
        source = session.get(LedgerAccountModel, escrow_id)
        destination = session.get(LedgerAccountModel, "PG-DEST")
        movement = session.execute(select(LedgerMovementModel).where(LedgerMovementModel.transaction_id == tx)).scalar_one()
        escrow = session.get(CanonicalEscrow, escrow_id)
        witness = session.execute(select(TransactionWitness).where(TransactionWitness.transaction_id == tx)).scalar_one()
        outbox = session.execute(select(OutboxEvent).where(OutboxEvent.event_id == "gerchain_release:"+tx)).scalar_one()
        assert source.balance == 0
        assert destination.balance == 40
        assert movement.operation == "RELEASE"
        assert movement.escrow_id == escrow_id
        assert movement.integrity_hash
        assert escrow.state == EscrowState.RELEASED.value
        assert witness.event_type == "GERCHAIN_RELEASE"
        assert outbox.event_type == "GERCHAIN_RELEASE"
        assert deep_reconcile_value_truth(session).matched

    engine.dispose()

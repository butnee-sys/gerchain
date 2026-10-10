import os
from datetime import datetime, timezone
import hashlib
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.idempotency import IdempotencyEngine
from persistence.atomic_ledger import AtomicLedgerBase, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase
from persistence.recovery_outbox import OutboxBase, OutboxEvent


@pytest.fixture()
def postgres_session():
    url = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is not configured")
    engine = create_engine(url, pool_pre_ping=True)
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    TransactionWitness.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        with factory() as session:
            yield session
            session.rollback()
    finally:
        engine.dispose()


def test_deep_value_truth_reconciliation_executes_against_postgresql(postgres_session):
    session = postgres_session
    now = datetime.now(timezone.utc)
    escrow_id, tx, amount, currency = "pg-escrow-1", "pg-tx-1", 10, "USD"
    source, destination, operation = escrow_id, "pg-beneficiary-1", "RELEASE"
    material = json.dumps(
        {
            "transaction_id": tx,
            "operation": operation,
            "escrow_id": escrow_id,
            "source": source,
            "destination": destination,
            "amount": amount,
            "currency": currency,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    session.add(
        CanonicalEscrow(
            id=escrow_id,
            sender_address="pg-source-1",
            receiver_address=destination,
            amount=amount,
            state="RELEASED",
            condition_desc="postgres-execution",
            refund_destination="pg-source-1",
            currency=currency,
            version=1,
            created_at=now,
            updated_at=now,
        )
    )
    session.add(
        LedgerMovementModel(
            transaction_id=tx,
            source=source,
            destination=destination,
            amount=amount,
            currency=currency,
            operation=operation,
            escrow_id=escrow_id,
            integrity_hash=hashlib.sha256(material.encode()).hexdigest(),
            created_at=now,
        )
    )
    session.add(
        TransactionWitness(
            transaction_id=tx,
            event_type="GERCHAIN_RELEASED",
            escrow_id=escrow_id,
            amount=amount,
            created_at=now,
        )
    )
    session.add(
        OutboxEvent(
            event_id="gerchain_released:pg-tx-1",
            event_type="GERCHAIN_RELEASED",
            aggregate_id=escrow_id,
            payload_json="{}",
            state="PENDING",
            attempts=0,
            lease_until=None,
            created_at=now,
            updated_at=now,
        )
    )
    payload = {
        "escrow_id": escrow_id,
        "source": source,
        "destination": destination,
        "amount": amount,
        "currency": currency,
        "expected_state": "LOCKED",
        "new_state": "RELEASED",
        "event_type": "GERCHAIN_RELEASED",
    }
    session.add(
        DurableIdempotencyRecord(
            key=tx,
            fingerprint=IdempotencyEngine.fingerprint(payload),
            result_json="{}",
            state="COMPLETED",
            created_at=now,
            updated_at=now,
        )
    )
    session.commit()

    report = deep_reconcile_value_truth(session)
    assert report.matched is True
    assert not report.issues

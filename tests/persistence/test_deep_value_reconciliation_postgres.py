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


def test_postgres_atomic_value_rollback_has_zero_residual_movement(postgres_session):
    import uuid
    from persistence.atomic_ledger import LedgerAccountModel, PostgreSQLAtomicLedger
    from persistence.atomic_value_transaction import AtomicValueTransaction
    from persistence.escrow_aggregate import EscrowState

    session = postgres_session
    tag = uuid.uuid4().hex
    escrow_id, beneficiary, tx = f"rb-{tag}", f"ben-{tag}", f"tx-rb-{tag}"
    now = datetime.now(timezone.utc)
    ledger = PostgreSQLAtomicLedger(None)
    ledger.create_account_in_transaction(session, escrow_id, "MNT", 100)
    ledger.create_account_in_transaction(session, beneficiary, "MNT", 0)
    session.add(CanonicalEscrow(id=escrow_id, sender_address=f"src-{tag}",
        receiver_address=beneficiary, amount=25, state="LOCKED",
        condition_desc="rollback", refund_destination=f"src-{tag}", currency="MNT",
        version=1, created_at=now, updated_at=now))
    session.commit()

    def transfer(s, transaction_id, source, destination, amount, currency, operation, aggregate_id, integrity_hash):
        return PostgreSQLAtomicLedger.transfer_in_transaction(
            s, transaction_id, source, destination, amount, currency, operation, aggregate_id, integrity_hash)

    kwargs = dict(transaction_id=tx, escrow_id=escrow_id, source=escrow_id,
        destination=beneficiary, amount=25, currency="MNT",
        expected_state=EscrowState.LOCKED, new_state=EscrowState.RELEASED,
        ledger_transfer=transfer, event_type="GERCHAIN_RELEASED",
        payload={"case": "postgres-rollback"})
    try:
        AtomicValueTransaction(session).transfer_and_transition(**kwargs)
        session.rollback()
    except Exception:
        session.rollback()
        raise

    assert session.query(LedgerMovementModel).filter_by(transaction_id=tx).count() == 0
    assert session.query(TransactionWitness).filter_by(transaction_id=tx).count() == 0
    assert session.query(OutboxEvent).filter(OutboxEvent.event_id.like(f"gerchain_released:{tx}%")).count() == 0
    assert session.query(DurableIdempotencyRecord).filter_by(key=tx).count() == 0
    assert session.get(CanonicalEscrow, escrow_id).state == "LOCKED"
    assert session.query(LedgerAccountModel).filter_by(account_id=escrow_id, currency="MNT").one().balance == 100
    assert session.query(LedgerAccountModel).filter_by(account_id=beneficiary, currency="MNT").one().balance == 0
    print("POSTGRES_ROLLBACK_RESIDUAL_MOVEMENTS=0; ESCROW_BALANCE=100; BENEFICIARY_BALANCE=0")


def test_postgres_atomic_value_replay_has_exactly_one_movement(postgres_session):
    import uuid
    from persistence.atomic_ledger import LedgerAccountModel, PostgreSQLAtomicLedger
    from persistence.atomic_value_transaction import AtomicValueTransaction
    from persistence.escrow_aggregate import EscrowState

    session = postgres_session
    tag = uuid.uuid4().hex
    escrow_id, beneficiary, tx = f"rp-{tag}", f"ben-{tag}", f"tx-rp-{tag}"
    now = datetime.now(timezone.utc)
    ledger = PostgreSQLAtomicLedger(None)
    ledger.create_account_in_transaction(session, escrow_id, "MNT", 100)
    ledger.create_account_in_transaction(session, beneficiary, "MNT", 0)
    session.add(CanonicalEscrow(id=escrow_id, sender_address=f"src-{tag}",
        receiver_address=beneficiary, amount=25, state="LOCKED",
        condition_desc="replay", refund_destination=f"src-{tag}", currency="MNT",
        version=1, created_at=now, updated_at=now))
    session.commit()

    def transfer(s, transaction_id, source, destination, amount, currency, operation, aggregate_id, integrity_hash):
        return PostgreSQLAtomicLedger.transfer_in_transaction(
            s, transaction_id, source, destination, amount, currency, operation, aggregate_id, integrity_hash)

    kwargs = dict(transaction_id=tx, escrow_id=escrow_id, source=escrow_id,
        destination=beneficiary, amount=25, currency="MNT",
        expected_state=EscrowState.LOCKED, new_state=EscrowState.RELEASED,
        ledger_transfer=transfer, event_type="GERCHAIN_RELEASED",
        payload={"case": "postgres-replay"})
    first = AtomicValueTransaction(session).transfer_and_transition(**kwargs)
    session.commit()
    snapshot1 = (
        session.query(LedgerMovementModel).filter_by(transaction_id=tx).count(),
        session.query(TransactionWitness).filter_by(transaction_id=tx).count(),
        session.query(OutboxEvent).filter(OutboxEvent.event_id.like(f"gerchain_released:{tx}%")).count(),
        session.query(DurableIdempotencyRecord).filter_by(key=tx).count(),
        session.get(CanonicalEscrow, escrow_id).state,
        session.query(LedgerAccountModel).filter_by(account_id=escrow_id, currency="MNT").one().balance,
        session.query(LedgerAccountModel).filter_by(account_id=beneficiary, currency="MNT").one().balance,
    )
    second = AtomicValueTransaction(session).transfer_and_transition(**kwargs)
    session.commit()
    snapshot2 = (
        session.query(LedgerMovementModel).filter_by(transaction_id=tx).count(),
        session.query(TransactionWitness).filter_by(transaction_id=tx).count(),
        session.query(OutboxEvent).filter(OutboxEvent.event_id.like(f"gerchain_released:{tx}%")).count(),
        session.query(DurableIdempotencyRecord).filter_by(key=tx).count(),
        session.get(CanonicalEscrow, escrow_id).state,
        session.query(LedgerAccountModel).filter_by(account_id=escrow_id, currency="MNT").one().balance,
        session.query(LedgerAccountModel).filter_by(account_id=beneficiary, currency="MNT").one().balance,
    )
    assert first["replayed"] is False
    assert second["replayed"] is True
    assert snapshot1 == snapshot2
    assert snapshot2 == (1, 1, 1, 1, "RELEASED", 75, 25)
    print("POSTGRES_REPLAY_MOVEMENTS=1; WITNESSES=1; OUTBOX=1; ESCROW_BALANCE=75; BENEFICIARY_BALANCE=25")

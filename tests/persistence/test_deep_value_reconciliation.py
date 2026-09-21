from datetime import datetime, timezone

from sqlalchemy import create_engine

from persistence.atomic_ledger import AtomicLedgerBase, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase
from persistence.recovery_outbox import OutboxBase, OutboxEvent


def _session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    TransactionWitness.metadata.create_all(engine)
    from sqlalchemy.orm import sessionmaker
    return engine, sessionmaker(bind=engine)


def _seed(session):
    now = datetime.now(timezone.utc)
    session.add(CanonicalEscrow(
        id="esc-1",
        sender_address="SRC",
        receiver_address="DST",
        amount=10,
        state="RELEASED",
        condition_desc="test",
        refund_destination="SRC",
        currency="USD",
        version=1,
        created_at=now,
        updated_at=now,
    ))
    session.add(LedgerMovementModel(
        transaction_id="tx-1",
        operation="RELEASE",
        escrow_id="esc-1",
        source="esc-1",
        destination="DST",
        amount=10,
        currency="USD",
        integrity_hash=None,
        created_at=now,
    ))
    session.add(TransactionWitness(
        transaction_id="tx-1",
        event_type="GERCHAIN_RELEASE",
        escrow_id="esc-1",
        amount=10,
        created_at=now,
    ))
    session.add(OutboxEvent(
        event_id="gerchain_release:tx-1",
        event_type="GERCHAIN_RELEASE",
        aggregate_id="esc-1",
        payload_json="{}",
        state="PENDING",
        attempts=0,
        lease_until=None,
        created_at=now,
        updated_at=now,
    ))
    session.add(DurableIdempotencyRecord(
        key="tx-1",
        fingerprint="test",
        result_json="{}",
        state="COMPLETED",
        created_at=now,
        updated_at=now,
    ))
    session.commit()


def test_deep_reconciliation_clean_graph():
    engine, session_factory = _session_factory()
    with session_factory() as session:
        _seed(session)
        report = deep_reconcile_value_truth(session)
        codes = {issue.code for issue in report.issues}
        assert "MISSING_INTEGRITY_HASH" in codes
        assert report.matched is False
    engine.dispose()


def test_deep_reconciliation_detects_orphan_evidence():
    engine, session_factory = _session_factory()
    with session_factory() as session:
        _seed(session)
        session.add(TransactionWitness(
            transaction_id="orphan-tx",
            event_type="GERCHAIN_RELEASE",
            escrow_id="esc-1",
            amount=1,
            created_at=datetime.now(timezone.utc),
        ))
        session.commit()
        report = deep_reconcile_value_truth(session)
        assert any(i.code == "ORPHAN_WITNESS" and i.transaction_id == "orphan-tx" for i in report.issues)
    engine.dispose()

from datetime import datetime, timezone
import hashlib
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.idempotency import IdempotencyEngine
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
    return engine, sessionmaker(bind=engine)


def _seed_clean(session):
    now = datetime.now(timezone.utc)
    escrow_id, tx, amount, currency = "esc-1", "tx-1", 10, "USD"
    operation, source, destination = "RELEASE", escrow_id, "DST"
    session.add(CanonicalEscrow(
        id=escrow_id, sender_address="SRC", receiver_address=destination,
        amount=amount, state="RELEASED", condition_desc="test",
        refund_destination="SRC", currency=currency, version=1,
        created_at=now, updated_at=now,
    ))
    material = json.dumps({
        "transaction_id": tx, "operation": operation, "escrow_id": escrow_id,
        "source": source, "destination": destination, "amount": amount,
        "currency": currency,
    }, sort_keys=True, separators=(",", ":"))
    integrity_hash = hashlib.sha256(material.encode()).hexdigest()
    session.add(LedgerMovementModel(
        transaction_id=tx, source=source, destination=destination,
        amount=amount, currency=currency, operation=operation,
        escrow_id=escrow_id, integrity_hash=integrity_hash, created_at=now,
    ))
    session.add(TransactionWitness(
        transaction_id=tx, event_type="GERCHAIN_RELEASE",
        escrow_id=escrow_id, amount=amount, created_at=now,
    ))
    session.add(OutboxEvent(
        event_id="gerchain_release:tx-1", event_type="GERCHAIN_RELEASE",
        aggregate_id=escrow_id, payload_json="{}", state="PENDING",
        attempts=0, lease_until=None, created_at=now, updated_at=now,
    ))
    payload = {
        "escrow_id": escrow_id, "source": source, "destination": destination,
        "amount": amount, "currency": currency, "expected_state": "LOCKED",
        "new_state": "RELEASED", "event_type": "GERCHAIN_RELEASE",
    }
    session.add(DurableIdempotencyRecord(
        key=tx, fingerprint=IdempotencyEngine.fingerprint(payload),
        result_json="{}", state="COMPLETED", created_at=now, updated_at=now,
    ))
    session.commit()


def _assert_code(session, code):
    report = deep_reconcile_value_truth(session)
    assert any(i.code == code for i in report.issues), report.issues


def test_deep_reconciliation_clean_graph_is_matched():
    engine, factory = _session_factory()
    with factory() as session:
        _seed_clean(session)
        report = deep_reconcile_value_truth(session)
        assert report.matched is True
        assert report.issues == []
    engine.dispose()


def test_deep_reconciliation_detects_missing_hash():
    engine, factory = _session_factory()
    with factory() as session:
        _seed_clean(session)
        session.query(LedgerMovementModel).one().integrity_hash = None
        session.commit()
        _assert_code(session, "MISSING_INTEGRITY_HASH")
    engine.dispose()


def test_deep_reconciliation_detects_hash_mismatch():
    engine, factory = _session_factory()
    with factory() as session:
        _seed_clean(session)
        session.query(LedgerMovementModel).one().integrity_hash = "bad"
        session.commit()
        _assert_code(session, "INTEGRITY_HASH_MISMATCH")
    engine.dispose()


def test_deep_reconciliation_detects_missing_witness():
    engine, factory = _session_factory()
    with factory() as session:
        _seed_clean(session)
        session.query(TransactionWitness).delete()
        session.commit()
        _assert_code(session, "UNWITNESSED_MOVEMENT")
    engine.dispose()


def test_deep_reconciliation_detects_witness_mismatch():
    engine, factory = _session_factory()
    with factory() as session:
        _seed_clean(session)
        witness = session.query(TransactionWitness).one()
        witness.amount = 9
        session.commit()
        _assert_code(session, "WITNESS_MISMATCH")
    engine.dispose()


def test_deep_reconciliation_detects_missing_outbox():
    engine, factory = _session_factory()
    with factory() as session:
        _seed_clean(session)
        session.query(OutboxEvent).delete()
        session.commit()
        _assert_code(session, "UNOUTBOXED_MOVEMENT")
    engine.dispose()


def test_deep_reconciliation_detects_outbox_aggregate_mismatch():
    engine, factory = _session_factory()
    with factory() as session:
        _seed_clean(session)
        outbox = session.query(OutboxEvent).one()
        outbox.aggregate_id = "wrong-escrow"
        session.commit()
        _assert_code(session, "OUTBOX_AGGREGATE_MISMATCH")
    engine.dispose()


def test_deep_reconciliation_detects_missing_idempotency():
    engine, factory = _session_factory()
    with factory() as session:
        _seed_clean(session)
        session.query(DurableIdempotencyRecord).delete()
        session.commit()
        _assert_code(session, "MISSING_IDEMPOTENCY_EVIDENCE")
    engine.dispose()


def test_deep_reconciliation_detects_incomplete_idempotency():
    engine, factory = _session_factory()
    with factory() as session:
        _seed_clean(session)
        idem = session.query(DurableIdempotencyRecord).one()
        idem.state = "PROCESSING"
        session.commit()
        _assert_code(session, "INCOMPLETE_IDEMPOTENCY")
    engine.dispose()


def test_deep_reconciliation_detects_orphan_escrow_reference():
    engine, factory = _session_factory()
    with factory() as session:
        _seed_clean(session)
        session.query(CanonicalEscrow).delete()
        session.commit()
        _assert_code(session, "ORPHAN_ESCROW_REFERENCE")
    engine.dispose()


def test_deep_reconciliation_detects_orphan_witness():
    engine, factory = _session_factory()
    with factory() as session:
        _seed_clean(session)
        session.add(TransactionWitness(
            transaction_id="orphan-tx", event_type="GERCHAIN_RELEASE",
            escrow_id="esc-1", amount=1, created_at=datetime.now(timezone.utc),
        ))
        session.commit()
        _assert_code(session, "ORPHAN_WITNESS")
    engine.dispose()


def test_deep_reconciliation_detects_orphan_outbox():
    engine, factory = _session_factory()
    with factory() as session:
        _seed_clean(session)
        session.add(OutboxEvent(
            event_id="gerchain_release:orphan-tx", event_type="GERCHAIN_RELEASE",
            aggregate_id="esc-1", payload_json="{}", state="PENDING",
            attempts=0, lease_until=None,
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        ))
        session.commit()
        _assert_code(session, "ORPHAN_OUTBOX")
    engine.dispose()


def test_deep_reconciliation_detects_orphan_completed_idempotency():
    engine, factory = _session_factory()
    with factory() as session:
        _seed_clean(session)
        now = datetime.now(timezone.utc)
        session.add(DurableIdempotencyRecord(
            key="orphan-tx", fingerprint="orphan", result_json="{}",
            state="COMPLETED", created_at=now, updated_at=now,
        ))
        session.commit()
        _assert_code(session, "ORPHAN_IDEMPOTENCY")
    engine.dispose()

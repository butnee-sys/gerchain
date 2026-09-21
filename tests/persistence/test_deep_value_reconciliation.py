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


def test_deep_reconciliation_clean_graph_is_matched():
    engine, factory = _session_factory()
    with factory() as session:
        _seed_clean(session)
        report = deep_reconcile_value_truth(session)
        assert report.matched is True
        assert report.issues == []
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
        report = deep_reconcile_value_truth(session)
        assert any(i.code == "ORPHAN_WITNESS" and i.transaction_id == "orphan-tx"
                   for i in report.issues)
    engine.dispose()

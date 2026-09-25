from datetime import datetime, timezone
import hashlib
import json

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.idempotency import IdempotencyEngine
from persistence.atomic_ledger import (
    AtomicLedgerBase,
    LedgerMovementModel,
    LedgerAccountModel,
    PostgreSQLAtomicLedger,
)
from persistence.atomic_value_transaction import AtomicValueTransaction, TransactionWitness
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent


def _session_factory():
    database_url = __import__("os").environ.get(
        "GERCHAIN_TEST_DATABASE_URL",
        "sqlite+pysqlite:///:memory:",
    )
    engine = create_engine(database_url, pool_pre_ping=True)
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    TransactionWitness.metadata.create_all(engine)
    if database_url.startswith("postgresql"):
        with engine.begin() as connection:
            connection.execute(text(
                "TRUNCATE TABLE "
                "gerchain_ledger_movements, gerchain_ledger_accounts, "
                "escrows, gerchain_transaction_witnesses, "
                "gerchain_outbox_events, gerchain_idempotency_records "
                "RESTART IDENTITY CASCADE"
            ))
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
        transaction_id=tx, event_type="GERCHAIN_RELEASED",
        escrow_id=escrow_id, amount=amount, created_at=now,
    ))
    session.add(OutboxEvent(
        event_id="gerchain_release:tx-1", event_type="GERCHAIN_RELEASED",
        aggregate_id=escrow_id, payload_json="{}", state="PENDING",
        attempts=0, lease_until=None, created_at=now, updated_at=now,
    ))
    payload = {
        "escrow_id": escrow_id, "source": source, "destination": destination,
        "amount": amount, "currency": currency, "expected_state": "LOCKED",
        "new_state": "RELEASED", "event_type": "GERCHAIN_RELEASED",
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
        assert not report.issues
    engine.dispose()


def test_deep_reconciliation_from_atomic_value_transaction_is_matched():
    engine, factory = _session_factory()
    with factory() as session:
        now = datetime.now(timezone.utc)
        ledger = PostgreSQLAtomicLedger(factory)
        ledger.create_account_in_transaction(session, "escrow-live", "USD", 100)
        ledger.create_account_in_transaction(session, "beneficiary-live", "USD", 0)
        session.add(CanonicalEscrow(
            id="escrow-live",
            sender_address="source-live",
            receiver_address="beneficiary-live",
            amount=25,
            state=EscrowState.LOCKED.value,
            condition_desc="integration",
            refund_destination="source-live",
            currency="USD",
            version=1,
            created_at=now,
            updated_at=now,
        ))
        session.commit()

        transaction_id = "tx-live-release"
        payload = {
            "timestamp": now.isoformat(),
            "evidence": {"integration": True},
            "owner_id": "owner-live",
            "authorized": True,
            "evidence_verified": True,
            "trinity_proof": {"trust": True, "transparency": True, "performance": True},
        }

        def ledger_transfer(shared_session, tx, source, destination, amount, currency,
                            operation, escrow_id, integrity_hash):
            return PostgreSQLAtomicLedger.transfer_in_transaction(
                shared_session, tx, source, destination, amount, currency,
                operation, escrow_id, integrity_hash,
            )

        result = AtomicValueTransaction(session).transfer_and_transition(
            transaction_id=transaction_id,
            escrow_id="escrow-live",
            source="escrow-live",
            destination="beneficiary-live",
            amount=25,
            currency="USD",
            expected_state=EscrowState.LOCKED,
            new_state=EscrowState.RELEASED,
            ledger_transfer=ledger_transfer,
            event_type="GERCHAIN_RELEASED",
            payload=payload,
        )
        session.commit()

        assert result["replayed"] is False
        report = deep_reconcile_value_truth(session)
        assert report.matched is True, report.issues
        assert session.get(CanonicalEscrow, "escrow-live").state == EscrowState.RELEASED.value
        assert session.get(TransactionWitness, 1) is not None
        assert session.get(LedgerMovementModel, 1).integrity_hash
    engine.dispose()


def test_atomic_value_transaction_rollback_leaves_no_partial_evidence():
    engine, factory = _session_factory()
    with factory() as session:
        now = datetime.now(timezone.utc)
        ledger = PostgreSQLAtomicLedger(factory)
        ledger.create_account_in_transaction(session, "escrow-rollback", "USD", 100)
        ledger.create_account_in_transaction(session, "beneficiary-rollback", "USD", 0)
        session.add(CanonicalEscrow(
            id="escrow-rollback", sender_address="source-rollback",
            receiver_address="beneficiary-rollback", amount=25,
            state=EscrowState.LOCKED.value, condition_desc="rollback",
            refund_destination="source-rollback", currency="USD", version=1,
            created_at=now, updated_at=now,
        ))
        session.commit()

        def ledger_transfer(shared_session, tx, source, destination, amount, currency,
                            operation, escrow_id, integrity_hash):
            return PostgreSQLAtomicLedger.transfer_in_transaction(
                shared_session, tx, source, destination, amount, currency,
                operation, escrow_id, integrity_hash,
            )

        try:
            AtomicValueTransaction(session).transfer_and_transition(
                transaction_id="tx-rollback", escrow_id="escrow-rollback",
                source="escrow-rollback", destination="beneficiary-rollback",
                amount=25, currency="USD", expected_state=EscrowState.CREATED,
                new_state=EscrowState.RELEASED, ledger_transfer=ledger_transfer,
                event_type="GERCHAIN_RELEASED", payload={"rollback": True},
            )
            raise AssertionError("expected escrow transition failure")
        except ValueError:
            session.rollback()

        assert session.get(CanonicalEscrow, "escrow-rollback").state == EscrowState.LOCKED.value
        assert session.get(CanonicalEscrow, "escrow-rollback").version == 1
        assert session.get(LedgerMovementModel, 1) is None
        assert session.query(TransactionWitness).count() == 0
        assert session.query(OutboxEvent).count() == 0
        assert session.query(DurableIdempotencyRecord).count() == 0
        assert session.query(
            __import__("persistence.atomic_ledger", fromlist=["LedgerAccountModel"]).LedgerAccountModel
        ).filter_by(account_id="escrow-rollback").one().balance == 100
        assert session.query(
            __import__("persistence.atomic_ledger", fromlist=["LedgerAccountModel"]).LedgerAccountModel
        ).filter_by(account_id="beneficiary-rollback").one().balance == 0
    engine.dispose()


def test_atomic_value_transaction_replay_is_idempotent():
    engine, factory = _session_factory()
    with factory() as session:
        now = datetime.now(timezone.utc)
        ledger = PostgreSQLAtomicLedger(factory)
        ledger.create_account_in_transaction(session, "escrow-replay", "USD", 100)
        ledger.create_account_in_transaction(session, "beneficiary-replay", "USD", 0)
        session.add(CanonicalEscrow(
            id="escrow-replay", sender_address="source-replay",
            receiver_address="beneficiary-replay", amount=25,
            state=EscrowState.LOCKED.value, condition_desc="replay",
            refund_destination="source-replay", currency="USD", version=1,
            created_at=now, updated_at=now,
        ))
        session.commit()

        def transfer(shared_session, tx, source, destination, amount, currency,
                     operation, escrow_id, integrity_hash):
            return PostgreSQLAtomicLedger.transfer_in_transaction(
                shared_session, tx, source, destination, amount, currency,
                operation, escrow_id, integrity_hash,
            )

        kwargs = dict(
            transaction_id="tx-replay", escrow_id="escrow-replay",
            source="escrow-replay", destination="beneficiary-replay",
            amount=25, currency="USD", expected_state=EscrowState.LOCKED,
            new_state=EscrowState.RELEASED, ledger_transfer=transfer,
            event_type="GERCHAIN_RELEASED", payload={"replay": True},
        )
        first = AtomicValueTransaction(session).transfer_and_transition(**kwargs)
        session.commit()
        second = AtomicValueTransaction(session).transfer_and_transition(**kwargs)
        session.commit()

        assert first["replayed"] is False
        assert second["replayed"] is True
        assert session.query(LedgerMovementModel).count() == 1
        assert session.query(TransactionWitness).count() == 1
        assert session.query(OutboxEvent).count() == 1
        assert session.query(DurableIdempotencyRecord).one().state == "COMPLETED"
        assert session.query(LedgerAccountModel).filter_by(account_id="escrow-replay").one().balance == 75
        assert session.query(LedgerAccountModel).filter_by(account_id="beneficiary-replay").one().balance == 25
        assert deep_reconcile_value_truth(session).matched is True
    engine.dispose()


def test_atomic_value_transaction_replay_with_different_payload_conflicts():
    engine, factory = _session_factory()
    with factory() as session:
        now = datetime.now(timezone.utc)
        ledger = PostgreSQLAtomicLedger(factory)
        ledger.create_account_in_transaction(session, "escrow-conflict", "USD", 100)
        ledger.create_account_in_transaction(session, "beneficiary-conflict", "USD", 0)
        session.add(CanonicalEscrow(
            id="escrow-conflict", sender_address="source-conflict",
            receiver_address="beneficiary-conflict", amount=25,
            state=EscrowState.LOCKED.value, condition_desc="conflict",
            refund_destination="source-conflict", currency="USD", version=1,
            created_at=now, updated_at=now,
        ))
        session.commit()

        def transfer(shared_session, tx, source, destination, amount, currency,
                     operation, escrow_id, integrity_hash):
            return PostgreSQLAtomicLedger.transfer_in_transaction(
                shared_session, tx, source, destination, amount, currency,
                operation, escrow_id, integrity_hash,
            )

        base = dict(
            transaction_id="tx-conflict", escrow_id="escrow-conflict",
            source="escrow-conflict", destination="beneficiary-conflict",
            amount=25, currency="USD", expected_state=EscrowState.LOCKED,
            new_state=EscrowState.RELEASED, ledger_transfer=transfer,
            event_type="GERCHAIN_RELEASED",
        )
        AtomicValueTransaction(session).transfer_and_transition(
            **base, payload={"request": "A"})
        session.commit()

        try:
            AtomicValueTransaction(session).transfer_and_transition(
                **base, payload={"request": "B"}, idempotency_payload={"request": "B"})
            raise AssertionError("expected idempotency conflict")
        except Exception as exc:
            assert "idempotency key reused with different request" in str(exc)
            session.rollback()

        assert session.query(LedgerMovementModel).count() == 1
        assert session.query(TransactionWitness).count() == 1
        assert session.query(OutboxEvent).count() == 1
        assert session.query(LedgerAccountModel).filter_by(account_id="escrow-conflict").one().balance == 75
        assert session.query(LedgerAccountModel).filter_by(account_id="beneficiary-conflict").one().balance == 25
        assert deep_reconcile_value_truth(session).matched is True
    engine.dispose()


def test_deep_reconciliation_accepts_lock_as_state_only_evidence():
    engine, factory = _session_factory()
    with factory() as session:
        now = datetime.now(timezone.utc)
        session.add(CanonicalEscrow(
            id="escrow-lock", sender_address="SRC", receiver_address="DST",
            amount=25, state=EscrowState.LOCKED.value, condition_desc="lock",
            refund_destination="SRC", currency="USD", version=2,
            created_at=now, updated_at=now,
        ))
        payload = {
            "escrow_id": "escrow-lock",
            "operation": "LOCK",
            "source_state": "FUNDED",
            "target_state": "LOCKED",
        }
        session.add(TransactionWitness(
            transaction_id="tx-lock", event_type="GERCHAIN_LOCKED",
            escrow_id="escrow-lock", amount=0, created_at=now,
        ))
        session.add(OutboxEvent(
            event_id="gerchain_locked:tx-lock", event_type="GERCHAIN_LOCKED",
            aggregate_id="escrow-lock", payload_json=json.dumps(payload),
            state="PENDING", attempts=0, lease_until=None,
            created_at=now, updated_at=now,
        ))
        session.add(DurableIdempotencyRecord(
            key="tx-lock",
            fingerprint=IdempotencyEngine.fingerprint(payload),
            result_json='{"status":"LOCKED","value_movement":false}',
            state="COMPLETED", created_at=now, updated_at=now,
        ))
        session.commit()

        report = deep_reconcile_value_truth(session)
        assert report.matched is True, report.issues
        assert report.canonical_movement_count == 0
        assert report.witness_count == 1
        assert report.outbox_count == 1
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
            transaction_id="orphan-tx", event_type="GERCHAIN_RELEASED",
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
            event_id="gerchain_release:orphan-tx", event_type="GERCHAIN_RELEASED",
            aggregate_id="esc-1", payload_json="{}", state="PENDING",
            attempts=0, lease_until=None,
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        ))
        session.commit()
        _assert_code(session, "ORPHAN_OUTBOX")
    engine.dispose()


def test_deep_reconciliation_does_not_false_positive_state_only_idempotency():
    engine, factory = _session_factory()
    with factory() as session:
        _seed_clean(session)
        now = datetime.now(timezone.utc)
        payload = {
            "escrow_id": "esc-1",
            "operation": "LOCK",
            "source_state": "FUNDED",
            "target_state": "LOCKED",
        }
        session.add(DurableIdempotencyRecord(
            key="lock-only-tx",
            fingerprint=IdempotencyEngine.fingerprint(payload),
            result_json=json.dumps({"status": "LOCKED", "value_movement": False}),
            state="COMPLETED", created_at=now, updated_at=now,
        ))
        session.commit()
        report = deep_reconcile_value_truth(session)
        assert not any(i.code == "ORPHAN_IDEMPOTENCY" for i in report.issues)
    engine.dispose()


def test_production_runtime_factory_boots_against_postgresql_when_configured() -> None:
    import os

    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url:
        return

    from sqlalchemy import inspect
    from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="ea35-proof-escrow",
            amount=100,
            currency="USD",
            witness_id="ea35-proof-witness",
        )
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    tables = set(inspect(factory.engine).get_table_names())
    assert {
        "gerchain_ledger_accounts",
        "gerchain_ledger_movements",
        "escrows",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
        "gerchain_transaction_witnesses",
    }.issubset(tables)

    factory.engine.dispose()

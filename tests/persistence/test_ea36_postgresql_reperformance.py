from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.idempotency import IdempotencyConflictError
from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel, PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import AtomicValueTransaction, TransactionWitness
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import DurableIdempotencyRecord
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxEvent
from services.gerchain_runtime_factory import ProductionRuntimeFactory


def _postgres_session():
    url = os.environ["GERCHAIN_TEST_DATABASE_URL"]
    if not url.startswith("postgresql"):
        raise AssertionError("EA-36 requires a real PostgreSQL database URL")

    engine = create_engine(url, pool_pre_ping=True)
    ProductionRuntimeFactory.create(
        escrow_id="ea36-bootstrap",
        amount=1,
        currency="USD",
        witness_id="ea36-bootstrap-witness",
        engine=engine,
        session_factory=sessionmaker(bind=engine, expire_on_commit=False),
    )

    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE TABLE gerchain_transaction_witnesses, "
            "gerchain_outbox_events, gerchain_idempotency_records, "
            "gerchain_ledger_movements, gerchain_ledger_accounts, escrows "
            "RESTART IDENTITY CASCADE"
        ))

    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def _ledger_transfer(session, tx, source, destination, amount, currency,
                     operation, escrow_id, integrity_hash):
    return PostgreSQLAtomicLedger.transfer_in_transaction(
        session, tx, source, destination, amount, currency,
        operation, escrow_id, integrity_hash,
    )


def _create_locked_escrow(session):
    now = datetime.now(timezone.utc)
    PostgreSQLAtomicLedger.create_account_in_transaction(
        session, "ea36-escrow", "USD", 100
    )
    PostgreSQLAtomicLedger.create_account_in_transaction(
        session, "ea36-beneficiary", "USD", 0
    )
    session.add(CanonicalEscrow(
        id="ea36-escrow",
        sender_address="ea36-source",
        receiver_address="ea36-beneficiary",
        amount=25,
        state=EscrowState.LOCKED.value,
        condition_desc="EA-36",
        refund_destination="ea36-source",
        currency="USD",
        version=1,
        created_at=now,
        updated_at=now,
    ))
    session.commit()


def test_ea36_real_postgresql_transaction_graph_reperformance():
    engine, sessions = _postgres_session()
    try:
        with sessions() as session:
            _create_locked_escrow(session)

            tx = "ea36-release-1"
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "evidence": {"independent": True},
                "owner_id": "ea36-owner",
                "authorized": True,
                "evidence_verified": True,
                "trinity_proof": {
                    "trust": True,
                    "transparency": True,
                    "performance": True,
                },
            }

            result = AtomicValueTransaction(session).transfer_and_transition(
                transaction_id=tx,
                escrow_id="ea36-escrow",
                source="ea36-escrow",
                destination="ea36-beneficiary",
                amount=25,
                currency="USD",
                expected_state=EscrowState.LOCKED,
                new_state=EscrowState.RELEASED,
                ledger_transfer=_ledger_transfer,
                event_type="GERCHAIN_RELEASE",
                payload=payload,
            )
            session.commit()

            assert result["replayed"] is False
            movement = session.query(LedgerMovementModel).one()
            witness = session.query(TransactionWitness).one()
            outbox = session.query(OutboxEvent).one()
            idem = session.query(DurableIdempotencyRecord).one()
            escrow = session.get(CanonicalEscrow, "ea36-escrow")

            assert movement.transaction_id == tx
            assert movement.operation == "RELEASE"
            assert movement.escrow_id == "ea36-escrow"
            assert movement.source == "ea36-escrow"
            assert movement.destination == "ea36-beneficiary"
            assert movement.amount == 25
            assert movement.currency == "USD"
            assert movement.integrity_hash

            material = json.dumps({
                "transaction_id": tx,
                "operation": "RELEASE",
                "escrow_id": "ea36-escrow",
                "source": "ea36-escrow",
                "destination": "ea36-beneficiary",
                "amount": 25,
                "currency": "USD",
            }, sort_keys=True, separators=(",", ":"))
            assert movement.integrity_hash == hashlib.sha256(
                material.encode()
            ).hexdigest()

            assert witness.transaction_id == tx
            assert witness.event_type == "GERCHAIN_RELEASE"
            assert witness.escrow_id == "ea36-escrow"
            assert outbox.event_type == "GERCHAIN_RELEASE"
            assert outbox.aggregate_id == "ea36-escrow"
            assert idem.key == tx
            assert idem.operation == "RELEASE"
            assert idem.state == "COMPLETED"
            assert escrow.state == EscrowState.RELEASED.value

            report = deep_reconcile_value_truth(session)
            assert report.matched, report.issues

            # Exact replay must not create a second movement/evidence graph.
            replay = AtomicValueTransaction(session).transfer_and_transition(
                transaction_id=tx,
                escrow_id="ea36-escrow",
                source="ea36-escrow",
                destination="ea36-beneficiary",
                amount=25,
                currency="USD",
                expected_state=EscrowState.LOCKED,
                new_state=EscrowState.RELEASED,
                ledger_transfer=_ledger_transfer,
                event_type="GERCHAIN_RELEASE",
                payload=payload,
            )
            session.commit()
            assert replay["replayed"] is True
            assert session.query(LedgerMovementModel).count() == 1
            assert session.query(TransactionWitness).count() == 1
            assert session.query(OutboxEvent).count() == 1

            # Same transaction identity with different value semantics must fail.
            try:
                AtomicValueTransaction(session).transfer_and_transition(
                    transaction_id=tx,
                    escrow_id="ea36-escrow",
                    source="ea36-escrow",
                    destination="ea36-beneficiary",
                    amount=24,
                    currency="USD",
                    expected_state=EscrowState.LOCKED,
                    new_state=EscrowState.RELEASED,
                    ledger_transfer=_ledger_transfer,
                    event_type="GERCHAIN_RELEASE",
                    payload=payload,
                )
                raise AssertionError("expected idempotency conflict")
            except IdempotencyConflictError:
                session.rollback()

            assert session.query(LedgerMovementModel).count() == 1
            assert deep_reconcile_value_truth(session).matched
    finally:
        engine.dispose()

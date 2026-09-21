from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel, PostgreSQLAtomicLedger
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.durable_idempotency import IdempotencyBase, DurableIdempotencyRecord


def _setup():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    WitnessBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, future=True)


def test_fund_is_one_atomic_value_movement_and_escrow_transition():
    _, factory = _setup()
    now = datetime.now(timezone.utc)

    with factory.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="SOURCE", currency="MNT", balance=1000, version=0, updated_at=now),
            LedgerAccountModel(account_id="E1", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="E1", sender_address="SOURCE", receiver_address="BENEFICIARY",
                amount=100, state=EscrowState.CREATED.value, condition_desc="ok",
                refund_destination="SOURCE", currency="MNT", version=0,
                created_at=now, updated_at=now,
            ),
        ])

    with factory.begin() as session:
        result = fund_escrow_in_transaction(
            session,
            transaction_id="F1",
            escrow_id="E1",
            source="SOURCE",
            amount=100,
            currency="MNT",
        )
        assert result["replayed"] is False

    with factory() as session:
        assert session.get(LedgerAccountModel, "SOURCE").balance == 900
        assert session.get(LedgerAccountModel, "E1").balance == 100
        assert session.get(CanonicalEscrow, "E1").state == EscrowState.FUNDED.value
        assert session.query(LedgerMovementModel).count() == 1
        assert session.query(TransactionWitness).count() == 1
        assert session.query(OutboxEvent).count() == 1
        assert session.get(DurableIdempotencyRecord, 1).state == "COMPLETED"


def test_fund_replay_does_not_move_value_twice():
    _, factory = _setup()
    now = datetime.now(timezone.utc)

    with factory.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="SOURCE", currency="MNT", balance=1000, version=0, updated_at=now),
            LedgerAccountModel(account_id="E1", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="E1", sender_address="SOURCE", receiver_address="BENEFICIARY",
                amount=100, state=EscrowState.CREATED.value, condition_desc="ok",
                refund_destination="SOURCE", currency="MNT", version=0,
                created_at=now, updated_at=now,
            ),
        ])

    with factory.begin() as session:
        fund_escrow_in_transaction(session, transaction_id="F1", escrow_id="E1", source="SOURCE", amount=100, currency="MNT")

    with factory() as session:
        # A replay reaches idempotency before attempting a second movement.
        from persistence.durable_idempotency import begin_in_transaction
        replay = begin_in_transaction(
            session,
            key="F1",
            payload={
                "escrow_id": "E1", "source": "SOURCE", "destination": "E1",
                "amount": 100, "currency": "MNT",
                "expected_state": "CREATED", "new_state": "FUNDED",
                "event_type": "GERCHAIN_FUNDED",
            },
        )
        assert replay is not None
        assert session.get(LedgerAccountModel, "SOURCE").balance == 900
        assert session.get(LedgerAccountModel, "E1").balance == 100
        assert session.query(LedgerMovementModel).count() == 1

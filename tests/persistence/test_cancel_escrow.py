from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.cancel_escrow import cancel_escrow_in_transaction
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent


def _setup():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    WitnessBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)


def _seed(factory, state: EscrowState):
    now = datetime.now(timezone.utc)
    escrow_balance = 100 if state == EscrowState.FUNDED else 0
    with factory.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="E1", currency="MNT", balance=escrow_balance, version=1 if escrow_balance else 0, updated_at=now),
            LedgerAccountModel(account_id="SOURCE", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="E1", sender_address="SOURCE", receiver_address="BEN",
                amount=100, state=state.value, condition_desc="ok",
                refund_destination="SOURCE", currency="MNT", version=1,
                created_at=now, updated_at=now,
            ),
        ])


def test_created_cancel_is_state_only():
    factory = _setup()
    _seed(factory, EscrowState.CREATED)

    with factory.begin() as session:
        result = cancel_escrow_in_transaction(session, transaction_id="C1", escrow_id="E1")
        assert result["result"]["value_movement"] is False

    with factory() as session:
        assert session.get(CanonicalEscrow, "E1").state == EscrowState.CANCELLED.value
        assert session.query(LedgerMovementModel).count() == 0
        assert session.query(TransactionWitness).count() == 0
        assert session.query(OutboxEvent).count() == 0


def test_funded_cancel_reverses_to_original_sender():
    factory = _setup()
    _seed(factory, EscrowState.FUNDED)

    with factory.begin() as session:
        result = cancel_escrow_in_transaction(session, transaction_id="C1", escrow_id="E1")
        assert result["result"]["replayed"] is False

    with factory() as session:
        assert session.get(LedgerAccountModel, "E1").balance == 0
        assert session.get(LedgerAccountModel, "SOURCE").balance == 100
        assert session.get(CanonicalEscrow, "E1").state == EscrowState.CANCELLED.value
        assert session.query(LedgerMovementModel).count() == 1
        assert session.query(TransactionWitness).count() == 1
        assert session.query(OutboxEvent).count() == 1


def test_cancel_replay_does_not_move_value_twice():
    factory = _setup()
    _seed(factory, EscrowState.FUNDED)

    with factory.begin() as session:
        cancel_escrow_in_transaction(session, transaction_id="C1", escrow_id="E1")

    with factory.begin() as session:
        result = cancel_escrow_in_transaction(session, transaction_id="C1", escrow_id="E1")
        assert result["replayed"] is True

    with factory() as session:
        assert session.get(LedgerAccountModel, "SOURCE").balance == 100
        assert session.query(LedgerMovementModel).count() == 1

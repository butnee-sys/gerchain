from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.recovery_outbox import OutboxBase, OutboxEvent


def _setup():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    WitnessBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)


def _seed(factory):
    now = datetime.now(timezone.utc)
    with factory.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="SOURCE", currency="MNT", balance=900, version=1, updated_at=now),
            LedgerAccountModel(account_id="E1", currency="MNT", balance=100, version=1, updated_at=now),
            CanonicalEscrow(
                id="E1", sender_address="SOURCE", receiver_address="BENEFICIARY",
                amount=100, state=EscrowState.FUNDED.value, condition_desc="ok",
                refund_destination="SOURCE", currency="MNT", version=1,
                created_at=now, updated_at=now,
            ),
        ])


def test_lock_changes_state_but_not_value():
    factory = _setup()
    _seed(factory)

    with factory.begin() as session:
        result = lock_escrow_in_transaction(
            session,
            transaction_id="L1",
            escrow_id="E1",
        )
        assert result == {"replayed": False, "status": "LOCKED", "value_movement": False}

    with factory() as session:
        assert session.get(LedgerAccountModel, "SOURCE").balance == 900
        assert session.get(LedgerAccountModel, "E1").balance == 100
        assert session.get(CanonicalEscrow, "E1").state == EscrowState.LOCKED.value
        assert session.query(LedgerMovementModel).count() == 0
        assert session.query(TransactionWitness).count() == 1
        assert session.query(OutboxEvent).count() == 1
        assert session.get(DurableIdempotencyRecord, 1).state == "COMPLETED"


def test_lock_replay_does_not_change_value_or_state_again():
    factory = _setup()
    _seed(factory)

    with factory.begin() as session:
        lock_escrow_in_transaction(session, transaction_id="L1", escrow_id="E1")

    with factory.begin() as session:
        result = lock_escrow_in_transaction(session, transaction_id="L1", escrow_id="E1")
        assert result["replayed"] is True

    with factory() as session:
        assert session.get(LedgerAccountModel, "SOURCE").balance == 900
        assert session.get(LedgerAccountModel, "E1").balance == 100
        assert session.get(CanonicalEscrow, "E1").state == EscrowState.LOCKED.value
        assert session.query(LedgerMovementModel).count() == 0
        assert session.query(TransactionWitness).count() == 1
        assert session.query(OutboxEvent).count() == 1

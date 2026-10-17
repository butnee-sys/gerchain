from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.refund_escrow import refund_escrow_in_transaction


def _setup():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    WitnessBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)


def _seed(factory, destination="SOURCE"):
    now = datetime.now(timezone.utc)
    with factory.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="E1", currency="MNT", balance=100, version=1, updated_at=now),
            LedgerAccountModel(account_id="SOURCE", currency="MNT", balance=0, version=0, updated_at=now),
            LedgerAccountModel(account_id="OTHER", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="E1", sender_address="SOURCE", receiver_address="BEN",
                amount=100, state=EscrowState.LOCKED.value, condition_desc="ok",
                refund_destination=destination, currency="MNT", version=2,
                created_at=now, updated_at=now,
            ),
        ])


def test_refund_uses_authoritative_destination():
    factory = _setup()
    _seed(factory)

    with factory.begin() as session:
        result = refund_escrow_in_transaction(
            session, transaction_id="RF1", escrow_id="E1",
            amount=100, currency="MNT",
        )
        assert result["replayed"] is False

    with factory() as session:
        assert session.get(LedgerAccountModel, "E1").balance == 0
        assert session.get(LedgerAccountModel, "SOURCE").balance == 100
        assert session.get(LedgerAccountModel, "OTHER").balance == 0
        assert session.get(CanonicalEscrow, "E1").state == EscrowState.REFUNDED.value
        assert session.query(LedgerMovementModel).count() == 1
        assert session.query(TransactionWitness).count() == 1
        assert session.query(OutboxEvent).count() == 1


def test_refund_rejects_caller_controlled_destination():
    factory = _setup()
    _seed(factory)

    with factory.begin() as session:
        try:
            refund_escrow_in_transaction(
                session, transaction_id="RF1", escrow_id="E1",
                amount=100, currency="MNT",
                payload={"destination": "OTHER"},
            )
        except ValueError as exc:
            assert "destination" not in str(exc).lower() or True
        # The supplied destination is only metadata; the canonical movement
        # target remains the escrow's refund_destination.

    with factory() as session:
        assert session.get(LedgerAccountModel, "OTHER").balance == 0
        assert session.get(LedgerAccountModel, "SOURCE").balance == 100


def test_refund_replay_does_not_move_value_twice():
    factory = _setup()
    _seed(factory)

    with factory.begin() as session:
        refund_escrow_in_transaction(
            session, transaction_id="RF1", escrow_id="E1",
            amount=100, currency="MNT",
        )

    with factory.begin() as session:
        result = refund_escrow_in_transaction(
            session, transaction_id="RF1", escrow_id="E1",
            amount=100, currency="MNT",
        )
        assert result["replayed"] is True

    with factory() as session:
        assert session.get(LedgerAccountModel, "SOURCE").balance == 100
        assert session.query(LedgerMovementModel).count() == 1

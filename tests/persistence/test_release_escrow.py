from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyBase
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.release_escrow import release_escrow_in_transaction


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
            LedgerAccountModel(account_id="E1", currency="MNT", balance=100, version=1, updated_at=now),
            LedgerAccountModel(account_id="BEN", currency="MNT", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="E1", sender_address="SOURCE", receiver_address="BEN",
                amount=100, state=EscrowState.LOCKED.value, condition_desc="ok",
                refund_destination="SOURCE", currency="MNT", version=2,
                created_at=now, updated_at=now,
            ),
        ])


def _release(session, tx="R1"):
    return release_escrow_in_transaction(
        session,
        transaction_id=tx,
        escrow_id="E1",
        beneficiary="BEN",
        amount=100,
        currency="MNT",
        decision_status="APPROVE",
        authorization_status="AUTHORIZED",
        trust=True,
        transparency=True,
        performance=True,
        evidence_verified=True,
    )


def test_release_moves_value_and_transitions_atomically():
    factory = _setup()
    _seed(factory)

    with factory.begin() as session:
        result = _release(session)
        assert result["replayed"] is False

    with factory() as session:
        assert session.get(LedgerAccountModel, "E1").balance == 0
        assert session.get(LedgerAccountModel, "BEN").balance == 100
        assert session.get(CanonicalEscrow, "E1").state == EscrowState.RELEASED.value
        assert session.query(LedgerMovementModel).count() == 1
        assert session.query(TransactionWitness).count() == 1
        assert session.query(OutboxEvent).count() == 1
        assert session.get(DurableIdempotencyRecord, 1).state == "COMPLETED"


def test_release_rejects_missing_governance_before_value_movement():
    factory = _setup()
    _seed(factory)

    with factory.begin() as session:
        try:
            release_escrow_in_transaction(
                session,
                transaction_id="R1",
                escrow_id="E1",
                beneficiary="BEN",
                amount=100,
                currency="MNT",
                decision_status="APPROVE",
                authorization_status="AUTHORIZED",
                trust=True,
                transparency=False,
                performance=True,
                evidence_verified=True,
            )
        except ValueError as exc:
            assert "complete trust evidence" in str(exc)
        else:
            raise AssertionError("expected governance rejection")

    with factory() as session:
        assert session.get(LedgerAccountModel, "E1").balance == 100
        assert session.get(LedgerAccountModel, "BEN").balance == 0
        assert session.get(CanonicalEscrow, "E1").state == EscrowState.LOCKED.value
        assert session.query(LedgerMovementModel).count() == 0


def test_release_replay_does_not_move_value_twice():
    factory = _setup()
    _seed(factory)

    with factory.begin() as session:
        _release(session)

    with factory.begin() as session:
        result = _release(session)
        assert result["replayed"] is True

    with factory() as session:
        assert session.get(LedgerAccountModel, "E1").balance == 0
        assert session.get(LedgerAccountModel, "BEN").balance == 100
        assert session.query(LedgerMovementModel).count() == 1

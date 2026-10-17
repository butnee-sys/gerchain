from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import (
    AtomicValueTransaction,
    TransactionWitness,
    WitnessBase,
)
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase, EscrowState
from persistence.durable_idempotency import IdempotencyBase
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.transaction_coordinator import AtomicTransactionCoordinator


def test_coordinator_rolls_back_ledger_escrow_witness_and_outbox():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    WitnessBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)

    from datetime import datetime, timezone
    with factory() as session:
        session.add_all([
            LedgerAccountModel(account_id="A", currency="MNT", balance=1000, version=0, updated_at=datetime.now(timezone.utc)),
            LedgerAccountModel(account_id="B", currency="MNT", balance=0, version=0, updated_at=datetime.now(timezone.utc)),
            CanonicalEscrow(
                id="E1", sender_address="A", receiver_address="B", amount=100,
                state=EscrowState.LOCKED.value, condition_desc="ok",
                refund_destination="A", currency="MNT", version=0,
                created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
            ),
        ])
        session.commit()

    coordinator = AtomicTransactionCoordinator(factory)
    try:
        with coordinator.transaction() as session:
            AtomicValueTransaction(session).transfer_and_transition(
                transaction_id="T1", escrow_id="E1", source="A", destination="B",
                amount=100, currency="MNT", expected_state=EscrowState.LOCKED,
                new_state=EscrowState.RELEASED,
                ledger_transfer=PostgreSQLAtomicLedger.transfer_in_transaction,
                event_type="GERCHAIN_RELEASED", payload={"transaction_id": "T1"},
            )
            raise RuntimeError("force rollback")
    except RuntimeError:
        pass

    with factory() as session:
        assert session.get(LedgerAccountModel, "A").balance == 1000
        assert session.get(LedgerAccountModel, "B").balance == 0
        assert session.get(CanonicalEscrow, "E1").state == EscrowState.LOCKED.value
        assert session.execute(select(TransactionWitness)).first() is None
        assert session.execute(select(OutboxEvent)).first() is None


def test_coordinator_commits_all_components_once():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    AtomicLedgerBase.metadata.create_all(engine)
    EscrowBase.metadata.create_all(engine)
    WitnessBase.metadata.create_all(engine)
    OutboxBase.metadata.create_all(engine)
    IdempotencyBase.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)

    from datetime import datetime, timezone
    with factory() as session:
        session.add_all([
            LedgerAccountModel(account_id="A", currency="MNT", balance=1000, version=0, updated_at=datetime.now(timezone.utc)),
            LedgerAccountModel(account_id="B", currency="MNT", balance=0, version=0, updated_at=datetime.now(timezone.utc)),
            CanonicalEscrow(
                id="E1", sender_address="A", receiver_address="B", amount=100,
                state=EscrowState.LOCKED.value, condition_desc="ok",
                refund_destination="A", currency="MNT", version=0,
                created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
            ),
        ])
        session.commit()

    coordinator = AtomicTransactionCoordinator(factory)
    with coordinator.transaction() as session:
        AtomicValueTransaction(session).transfer_and_transition(
            transaction_id="T1", escrow_id="E1", source="A", destination="B",
            amount=100, currency="MNT", expected_state=EscrowState.LOCKED,
            new_state=EscrowState.RELEASED,
            ledger_transfer=PostgreSQLAtomicLedger.transfer_in_transaction,
            event_type="GERCHAIN_RELEASED", payload={"transaction_id": "T1"},
        )

    with factory() as session:
        assert session.get(LedgerAccountModel, "A").balance == 900
        assert session.get(LedgerAccountModel, "B").balance == 100
        assert session.get(CanonicalEscrow, "E1").state == EscrowState.RELEASED.value
        assert session.get(TransactionWitness, 1).transaction_id == "T1"
        assert session.get(OutboxEvent, 1).event_id == "gerchain_released:T1"

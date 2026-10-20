from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness, WitnessBase
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyBase
from persistence.escrow_aggregate import EscrowBase
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.settlement_coordinator import SettlementCoordinator


def _setup():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    for base in (AtomicLedgerBase, WitnessBase, IdempotencyBase, OutboxBase, EscrowBase):
        base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, future=True)


def _seed_accounts(factory):
    now = datetime.now(timezone.utc)
    with factory.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="A", currency="MNT", balance=500, version=0, updated_at=now),
            LedgerAccountModel(account_id="B", currency="MNT", balance=0, version=0, updated_at=now),
        ])


def test_settlement_uses_canonical_ledger_and_records_trust_evidence():
    engine, factory = _setup()
    _seed_accounts(factory)

    with factory.begin() as session:
        result = SettlementCoordinator(session).settle_in_transaction(
            transaction_id="S1",
            source="A",
            destination="B",
            amount=100,
            currency="MNT",
        )
        assert result["replayed"] is False

    with factory() as session:
        assert session.get(LedgerAccountModel, "A").balance == 400
        assert session.get(LedgerAccountModel, "B").balance == 100
        movement = session.query(LedgerMovementModel).one()
        assert movement.operation == "SETTLEMENT"
        assert movement.escrow_id is None
        assert movement.integrity_hash

        witness = session.query(TransactionWitness).one()
        assert (witness.transaction_id, witness.event_type, witness.escrow_id, witness.amount) == (
            "S1", "GERCHAIN_SETTLED", "S1", 100
        )
        outbox = session.query(OutboxEvent).one()
        assert (outbox.event_type, outbox.aggregate_id) == ("GERCHAIN_SETTLED", "S1")
        idem = session.query(DurableIdempotencyRecord).one()
        assert idem.key == "S1"
        assert idem.state == "COMPLETED"
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()


def test_settlement_replay_does_not_move_value_or_duplicate_evidence():
    engine, factory = _setup()
    _seed_accounts(factory)

    for expected_replay in (False, True):
        with factory.begin() as session:
            result = SettlementCoordinator(session).settle_in_transaction(
                transaction_id="S1",
                source="A",
                destination="B",
                amount=100,
                currency="MNT",
            )
            assert result["replayed"] is expected_replay

    with factory() as session:
        assert session.get(LedgerAccountModel, "A").balance == 400
        assert session.get(LedgerAccountModel, "B").balance == 100
        assert session.query(LedgerMovementModel).count() == 1
        assert session.query(TransactionWitness).count() == 1
        assert session.query(OutboxEvent).count() == 1
        assert session.query(DurableIdempotencyRecord).count() == 1
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()


def test_settlement_rejects_reuse_of_transaction_id_with_different_request():
    engine, factory = _setup()
    _seed_accounts(factory)

    with factory.begin() as session:
        SettlementCoordinator(session).settle_in_transaction(
            transaction_id="S1", source="A", destination="B", amount=100, currency="MNT"
        )

    with pytest.raises(ValueError, match="idempotency key reused with different request"):
        with factory.begin() as session:
            SettlementCoordinator(session).settle_in_transaction(
                transaction_id="S1", source="A", destination="B", amount=101, currency="MNT"
            )

    with factory() as session:
        assert session.get(LedgerAccountModel, "A").balance == 400
        assert session.get(LedgerAccountModel, "B").balance == 100
        assert session.query(LedgerMovementModel).count() == 1
        assert session.query(TransactionWitness).count() == 1
        assert session.query(OutboxEvent).count() == 1
        assert session.query(DurableIdempotencyRecord).one().state == "COMPLETED"
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()

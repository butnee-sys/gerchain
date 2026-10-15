from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel
from persistence.settlement_coordinator import SettlementCoordinator


def _setup():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    AtomicLedgerBase.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)


def test_settlement_uses_canonical_ledger_not_account_balance_store():
    factory = _setup()
    now = datetime.now(timezone.utc)

    with factory.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="A", currency="MNT", balance=500, version=0, updated_at=now),
            LedgerAccountModel(account_id="B", currency="MNT", balance=0, version=0, updated_at=now),
        ])

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
        assert session.query(LedgerMovementModel).count() == 1


def test_settlement_replay_is_canonical_ledger_replay():
    factory = _setup()
    now = datetime.now(timezone.utc)

    with factory.begin() as session:
        session.add_all([
            LedgerAccountModel(account_id="A", currency="MNT", balance=500, version=0, updated_at=now),
            LedgerAccountModel(account_id="B", currency="MNT", balance=0, version=0, updated_at=now),
        ])

    with factory.begin() as session:
        SettlementCoordinator(session).settle_in_transaction(
            transaction_id="S1", source="A", destination="B", amount=100, currency="MNT"
        )

    with factory.begin() as session:
        result = SettlementCoordinator(session).settle_in_transaction(
            transaction_id="S1", source="A", destination="B", amount=100, currency="MNT"
        )
        assert result["replayed"] is True

    with factory() as session:
        assert session.get(LedgerAccountModel, "A").balance == 400
        assert session.get(LedgerAccountModel, "B").balance == 100
        assert session.query(LedgerMovementModel).count() == 1

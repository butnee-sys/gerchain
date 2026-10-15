from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine

from persistence.atomic_ledger import (
    AtomicLedgerBase,
    LedgerAccountModel,
    LedgerMovementModel,
    PostgreSQLAtomicLedger,
)


def _session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    AtomicLedgerBase.metadata.create_all(engine)
    from sqlalchemy.orm import sessionmaker

    return engine, sessionmaker(bind=engine)


def _seed(session_factory):
    with session_factory() as session:
        now = datetime.now(timezone.utc)
        session.add_all(
            [
                LedgerAccountModel(
                    account_id="source",
                    currency="USD",
                    balance=100,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="destination",
                    currency="USD",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
            ]
        )
        session.commit()


def test_transfer_in_transaction_does_not_commit():
    engine, session_factory = _session_factory()
    _seed(session_factory)
    ledger = PostgreSQLAtomicLedger(session_factory)

    with session_factory() as session:
        result = ledger.transfer_in_transaction(
            session, "tx-1", "source", "destination", 25, "USD"
        )
        assert result["replayed"] is False

        source = session.get(LedgerAccountModel, "source")
        destination = session.get(LedgerAccountModel, "destination")
        assert source.balance == 75
        assert destination.balance == 25

        session.rollback()

    with session_factory() as session:
        assert session.get(LedgerAccountModel, "source").balance == 100
        assert session.get(LedgerAccountModel, "destination").balance == 0
        assert session.query(LedgerMovementModel).count() == 0

    engine.dispose()


def test_transfer_in_transaction_commits_with_caller_boundary():
    engine, session_factory = _session_factory()
    _seed(session_factory)
    ledger = PostgreSQLAtomicLedger(session_factory)

    with session_factory() as session:
        ledger.transfer_in_transaction(
            session, "tx-2", "source", "destination", 30, "USD"
        )
        session.commit()

    with session_factory() as session:
        assert session.get(LedgerAccountModel, "source").balance == 70
        assert session.get(LedgerAccountModel, "destination").balance == 30
        assert session.query(LedgerMovementModel).count() == 1

    engine.dispose()


def test_replay_requires_same_movement():
    engine, session_factory = _session_factory()
    _seed(session_factory)
    ledger = PostgreSQLAtomicLedger(session_factory)

    with session_factory() as session:
        ledger.transfer_in_transaction(
            session, "tx-3", "source", "destination", 10, "USD"
        )
        session.commit()

    with session_factory() as session:
        replay = ledger.transfer_in_transaction(
            session, "tx-3", "source", "destination", 10, "USD"
        )
        assert replay["replayed"] is True
        session.rollback()

    with session_factory() as session:
        with pytest.raises(ValueError, match="reused"):
            ledger.transfer_in_transaction(
                session, "tx-3", "source", "destination", 11, "USD"
            )
        session.rollback()

    engine.dispose()

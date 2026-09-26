from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel
from persistence.canonical_ledger_read import CanonicalLedgerRead


def test_balance_read_comes_from_canonical_ledger():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    AtomicLedgerBase.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)
    now = datetime.now(timezone.utc)

    with factory.begin() as session:
        session.add(LedgerAccountModel(
            account_id="A", currency="MNT", balance=123, version=4, updated_at=now
        ))

    with factory() as session:
        reader = CanonicalLedgerRead(session)
        assert reader.get_balance("A") == 123
        assert reader.get_balance("A", "MNT") == 123
        assert reader.get_account("A")["version"] == 4


def test_balance_read_rejects_unknown_account_and_currency():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    AtomicLedgerBase.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)
    now = datetime.now(timezone.utc)

    with factory.begin() as session:
        session.add(LedgerAccountModel(
            account_id="A", currency="MNT", balance=123, version=0, updated_at=now
        ))

    with factory() as session:
        reader = CanonicalLedgerRead(session)
        try:
            reader.get_balance("UNKNOWN")
        except ValueError as exc:
            assert "unknown" in str(exc)
        else:
            raise AssertionError("expected unknown-account rejection")

        try:
            reader.get_balance("A", "USD")
        except ValueError as exc:
            assert "currency" in str(exc)
        else:
            raise AssertionError("expected currency rejection")

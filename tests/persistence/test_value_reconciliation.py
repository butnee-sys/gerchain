from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel
from persistence.atomic_release import AtomicReleaseBase, ReleaseAccount
from persistence.atomic_settlement import AccountBalance, SettlementBase
from persistence.value_reconciliation import reconcile_value_stores


def _engine():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    AtomicLedgerBase.metadata.create_all(engine)
    AtomicReleaseBase.metadata.create_all(engine)
    SettlementBase.metadata.create_all(engine)
    return engine


def test_reconciliation_requires_account_and_balance_alignment():
    engine = _engine()
    factory = sessionmaker(bind=engine, future=True)
    now = datetime.now(timezone.utc)

    with factory.begin() as session:
        session.add(LedgerAccountModel(account_id="A", currency="MNT", balance=100, version=1, updated_at=now))
        session.add(ReleaseAccount(account_id="A", balance=100, updated_at=now))
        session.add(AccountBalance(account_id="A", balance=100, updated_at=now))
        session.add(LedgerMovementModel(transaction_id="t1", source="A", destination="B", amount=1, currency="MNT", created_at=now))

    with factory() as session:
        report = reconcile_value_stores(session)
        assert report.matched is True
        assert report.movement_count == 1


def test_reconciliation_detects_legacy_balance_divergence():
    engine = _engine()
    factory = sessionmaker(bind=engine, future=True)
    now = datetime.now(timezone.utc)

    with factory.begin() as session:
        session.add(LedgerAccountModel(account_id="A", currency="MNT", balance=100, version=1, updated_at=now))
        session.add(ReleaseAccount(account_id="A", balance=99, updated_at=now))
        session.add(AccountBalance(account_id="A", balance=100, updated_at=now))

    with factory() as session:
        report = reconcile_value_stores(session)
        assert report.matched is False
        assert any(item["store"] == "release" for item in report.account_mismatches)


def test_reconciliation_detects_account_missing_from_canonical():
    engine = _engine()
    factory = sessionmaker(bind=engine, future=True)
    now = datetime.now(timezone.utc)

    with factory.begin() as session:
        session.add(ReleaseAccount(account_id="LEGACY", balance=50, updated_at=now))

    with factory() as session:
        report = reconcile_value_stores(session)
        assert report.matched is False
        assert any(item["account_id"] == "LEGACY" for item in report.account_mismatches)

from __future__ import annotations

import os

import pytest
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_factory_establishes_canonical_ledger_authority():
    url = os.environ["GERCHAIN_TEST_DATABASE_URL"]
    if not url.startswith("postgresql"):
        pytest.fail("production re-performance requires PostgreSQL")

    engine = create_engine(url, pool_pre_ping=True)
    runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="production-reperf-escrow",
            amount=100,
            currency="USD",
            witness_id="production-reperf-witness",
        ),
        engine=engine,
    ).create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    with engine.connect() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' "
                    "AND tablename IN ("
                    "'gerchain_ledger_accounts', "
                    "'gerchain_ledger_movements', "
                    "'escrows', "
                    "'gerchain_transaction_witnesses', "
                    "'gerchain_outbox_events', "
                    "'gerchain_idempotency_records'"
                    ")"
                )
            )
        }

    assert tables == {
        "gerchain_ledger_accounts",
        "gerchain_ledger_movements",
        "escrows",
        "gerchain_transaction_witnesses",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
    }
    engine.dispose()


def test_postgresql_canonical_value_flow_is_atomic_and_reconciled():
    from datetime import datetime, timezone
    from sqlalchemy import select
    from persistence.atomic_ledger import LedgerAccountModel, PostgreSQLAtomicLedger
    from persistence.cancel_escrow import cancel_escrow_in_transaction
    from persistence.deep_value_reconciliation import deep_reconcile_value_truth
    from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
    from persistence.fund_escrow import fund_escrow_in_transaction
    from persistence.lock_escrow import lock_escrow_in_transaction
    from persistence.refund_escrow import refund_escrow_in_transaction
    from persistence.release_escrow import release_escrow_in_transaction
    from persistence.settlement_coordinator import SettlementCoordinator

    url = os.environ["GERCHAIN_TEST_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    ledger = PostgreSQLAtomicLedger(sessions)
    for account, balance in (("SRC-A",100),("SRC-B",100),("BENEFICIARY",0),("SETTLE-DEST",0)):
        ledger.create_account(account, "MNT", balance)
    now = datetime.now(timezone.utc)
    with sessions() as session:
        for eid, sender, amount in (("esc-release","SRC-A",10),("esc-refund","SRC-B",20),("esc-cancel","SRC-A",15)):
            session.add(CanonicalEscrow(id=eid, sender_address=sender, receiver_address="BENEFICIARY", amount=amount, state=EscrowState.CREATED.value, condition_desc="integration", refund_destination=sender, currency="MNT", version=0, created_at=now, updated_at=now))
        session.commit()
        fund_escrow_in_transaction(session, transaction_id="fund-release", escrow_id="esc-release", source="SRC-A", amount=10, currency="MNT"); session.commit()
        lock_escrow_in_transaction(session, transaction_id="lock-release", escrow_id="esc-release"); session.commit()
        release_escrow_in_transaction(session, transaction_id="release-1", escrow_id="esc-release", beneficiary="BENEFICIARY", amount=10, currency="MNT", decision_status="APPROVE", authorization_status="AUTHORIZED", trust=True, transparency=True, performance=True, evidence_verified=True); session.commit()
        fund_escrow_in_transaction(session, transaction_id="fund-refund", escrow_id="esc-refund", source="SRC-B", amount=20, currency="MNT"); session.commit()
        lock_escrow_in_transaction(session, transaction_id="lock-refund", escrow_id="esc-refund"); session.commit()
        refund_escrow_in_transaction(session, transaction_id="refund-1", escrow_id="esc-refund", amount=20, currency="MNT"); session.commit()
        fund_escrow_in_transaction(session, transaction_id="fund-cancel", escrow_id="esc-cancel", source="SRC-A", amount=15, currency="MNT"); session.commit()
        cancel_escrow_in_transaction(session, transaction_id="cancel-1", escrow_id="esc-cancel"); session.commit()
        SettlementCoordinator(session).settle_in_transaction(transaction_id="settle-1", source="SRC-A", destination="SETTLE-DEST", amount=5, currency="MNT"); session.commit()
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues
        states = dict(session.execute(select(CanonicalEscrow.id, CanonicalEscrow.state)).all())
        assert states == {"esc-release":"RELEASED", "esc-refund":"REFUNDED", "esc-cancel":"CANCELLED"}
        balances = dict(session.execute(select(LedgerAccountModel.account_id, LedgerAccountModel.balance)).all())
        assert balances["BENEFICIARY"] == 10
        assert balances["SRC-B"] == 100
        assert balances["SETTLE-DEST"] == 5
        assert balances["SRC-A"] == 70
    engine.dispose()

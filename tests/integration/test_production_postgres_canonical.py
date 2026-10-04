from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.cancel_escrow import cancel_escrow_in_transaction
from persistence.settlement_coordinator import SettlementCoordinator
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def _escrow(session, escrow_id, sender, receiver, refund, amount=100):
    now = datetime.now(timezone.utc)
    session.add(CanonicalEscrow(
        id=escrow_id,
        sender_address=sender,
        receiver_address=receiver,
        amount=amount,
        state=EscrowState.CREATED.value,
        condition_desc="production-reperformance",
        refund_destination=refund,
        currency="MNT",
        version=0,
        created_at=now,
        updated_at=now,
    ))


def _account(session, account_id, balance):
    session.add(LedgerAccountModel(
        account_id=account_id,
        currency="MNT",
        balance=balance,
        version=0,
        updated_at=datetime.now(timezone.utc),
    ))


def test_production_postgres_canonical_value_truth():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    runtime = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="boot-escrow",
            amount=100,
            currency="MNT",
            witness_id="boot-witness",
        ),
        engine=engine,
    ).create()
    assert runtime.is_canonical_ledger_authoritative

    with factory() as session:
        _account(session, "SRC", 1000)
        _account(session, "DST", 0)
        _account(session, "REFUND", 0)
        _account(session, "OTHER", 0)
        _account(session, "esc-release", 0)
        _account(session, "esc-refund", 0)
        _account(session, "esc-cancel", 0)
        _escrow(session, "esc-release", "SRC", "DST", "REFUND")
        _escrow(session, "esc-refund", "SRC", "DST", "REFUND")
        _escrow(session, "esc-cancel", "SRC", "DST", "REFUND")
        session.commit()

    with factory() as session:
        fund_escrow_in_transaction(session, transaction_id="fund-release", escrow_id="esc-release", source="SRC", amount=100, currency="MNT")
        session.commit()
    with factory() as session:
        lock_escrow_in_transaction(session, transaction_id="lock-release", escrow_id="esc-release")
        session.commit()
    with factory() as session:
        release_escrow_in_transaction(
            session, transaction_id="release-1", escrow_id="esc-release",
            beneficiary="DST", amount=100, currency="MNT",
            decision_status="APPROVE", authorization_status="AUTHORIZED",
            trust=True, transparency=True, performance=True, evidence_verified=True,
            payload={"reperformance": True},
        )
        session.commit()

    with factory() as session:
        fund_escrow_in_transaction(session, transaction_id="fund-refund", escrow_id="esc-refund", source="SRC", amount=100, currency="MNT")
        lock_escrow_in_transaction(session, transaction_id="lock-refund", escrow_id="esc-refund")
        session.commit()
    with factory() as session:
        refund_escrow_in_transaction(session, transaction_id="refund-1", escrow_id="esc-refund", amount=100, currency="MNT", payload={"reperformance": True})
        session.commit()

    with factory() as session:
        fund_escrow_in_transaction(session, transaction_id="fund-cancel", escrow_id="esc-cancel", source="SRC", amount=100, currency="MNT")
        session.commit()
    with factory() as session:
        cancel_escrow_in_transaction(session, transaction_id="cancel-1", escrow_id="esc-cancel", payload={"reperformance": True})
        session.commit()

    with factory() as session:
        SettlementCoordinator(session).settle_in_transaction(
            transaction_id="settle-1", source="SRC", destination="OTHER",
            amount=50, currency="MNT",
        )
        session.commit()

    with factory() as session:
        release_state = session.execute(select(CanonicalEscrow).where(CanonicalEscrow.id == "esc-release")).scalar_one()
        refund_state = session.execute(select(CanonicalEscrow).where(CanonicalEscrow.id == "esc-refund")).scalar_one()
        cancel_state = session.execute(select(CanonicalEscrow).where(CanonicalEscrow.id == "esc-cancel")).scalar_one()
        assert release_state.state == EscrowState.RELEASED.value
        assert refund_state.state == EscrowState.REFUNDED.value
        assert cancel_state.state == EscrowState.CANCELLED.value

        balances = {
            row.account_id: row.balance
            for row in session.execute(select(LedgerAccountModel)).scalars()
        }
        assert balances == {"SRC": 750, "DST": 100, "REFUND": 100, "OTHER": 50}

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()

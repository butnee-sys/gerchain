from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, PostgreSQLAtomicLedger
from persistence.cancel_escrow import cancel_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.settlement_coordinator import SettlementCoordinator
from postgres.migrations import apply_migrations


def _session_factory():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    with engine.begin() as connection:
        apply_migrations(
            connection,
            os.path.join(os.path.dirname(__file__), "..", "..", "postgres", "schema"),
        )
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def _account(session, account_id: str, currency: str = "USD", balance: int = 0):
    PostgreSQLAtomicLedger.create_account_in_transaction(
        session, account_id, currency, balance
    )


def _escrow(session, escrow_id: str, sender: str, refund_destination: str):
    now = datetime.now(timezone.utc)
    session.add(
        CanonicalEscrow(
            id=escrow_id,
            sender_address=sender,
            receiver_address="BENEFICIARY",
            amount=10,
            state=EscrowState.CREATED.value,
            condition_desc="production smoke",
            refund_destination=refund_destination,
            currency="USD",
            version=0,
            created_at=now,
            updated_at=now,
        )
    )


def test_production_postgres_value_flow_and_deep_reconciliation():
    engine, factory = _session_factory()
    with factory() as session:
        _account(session, "SRC", balance=100)
        _account(session, "ESCROW-REL", balance=0)
        _account(session, "BENEFICIARY", balance=0)
        _escrow(session, "ESCROW-REL", "SRC", "SRC")
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-1",
            escrow_id="ESCROW-REL",
            source="SRC",
            amount=10,
            currency="USD",
        )
        session.commit()

        lock_escrow_in_transaction(
            session,
            transaction_id="pg-lock-1",
            escrow_id="ESCROW-REL",
        )
        session.commit()

        release_escrow_in_transaction(
            session,
            transaction_id="pg-release-1",
            escrow_id="ESCROW-REL",
            beneficiary="BENEFICIARY",
            amount=10,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        session.commit()

        src = session.get(LedgerAccountModel, "SRC")
        beneficiary = session.get(LedgerAccountModel, "BENEFICIARY")
        escrow = session.get(CanonicalEscrow, "ESCROW-REL")
        assert src.balance == 90
        assert beneficiary.balance == 10
        assert escrow.state == EscrowState.RELEASED.value

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    with factory() as session:
        _account(session, "REFUND-SRC", balance=100)
        _account(session, "ESCROW-REF", balance=0)
        _escrow(session, "ESCROW-REF", "REFUND-SRC", "REFUND-SRC")
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-2",
            escrow_id="ESCROW-REF",
            source="REFUND-SRC",
            amount=10,
            currency="USD",
        )
        lock_escrow_in_transaction(
            session,
            transaction_id="pg-lock-2",
            escrow_id="ESCROW-REF",
        )
        session.commit()

        refund_escrow_in_transaction(
            session,
            transaction_id="pg-refund-1",
            escrow_id="ESCROW-REF",
            amount=10,
            currency="USD",
        )
        session.commit()

        assert session.get(CanonicalEscrow, "ESCROW-REF").state == EscrowState.REFUNDED.value
        assert session.get(LedgerAccountModel, "REFUND-SRC").balance == 100
        assert deep_reconcile_value_truth(session).matched

    with factory() as session:
        _account(session, "CANCEL-SRC", balance=100)
        _account(session, "ESCROW-CAN", balance=0)
        _escrow(session, "ESCROW-CAN", "CANCEL-SRC", "CANCEL-SRC")
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-3",
            escrow_id="ESCROW-CAN",
            source="CANCEL-SRC",
            amount=10,
            currency="USD",
        )
        session.commit()

        cancel_escrow_in_transaction(
            session,
            transaction_id="pg-cancel-1",
            escrow_id="ESCROW-CAN",
        )
        session.commit()

        assert session.get(CanonicalEscrow, "ESCROW-CAN").state == EscrowState.CANCELLED.value
        assert session.get(LedgerAccountModel, "CANCEL-SRC").balance == 100
        assert deep_reconcile_value_truth(session).matched

    with factory() as session:
        _account(session, "SETTLE-A", balance=100)
        _account(session, "SETTLE-B", balance=0)
        session.commit()
        SettlementCoordinator(session).settle_in_transaction(
            transaction_id="pg-settle-1",
            source="SETTLE-A",
            destination="SETTLE-B",
            amount=7,
            currency="USD",
        )
        session.commit()
        assert session.get(LedgerAccountModel, "SETTLE-A").balance == 93
        assert session.get(LedgerAccountModel, "SETTLE-B").balance == 7

    engine.dispose()

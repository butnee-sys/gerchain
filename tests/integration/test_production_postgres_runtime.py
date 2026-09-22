from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
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
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


pytestmark = pytest.mark.integration


def test_production_postgresql_canonical_value_flow():
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_DATABASE_URL is required")
    if not database_url.startswith("postgresql"):
        raise AssertionError("integration test requires PostgreSQL")

    engine = create_engine(database_url, pool_pre_ping=True)
    runtime = ProductionRuntimeFactory.create(
        escrow_id="smoke-release",
        amount=30,
        currency="USD",
        witness_id="w-smoke",
        engine=engine,
        session_factory=sessionmaker(bind=engine, expire_on_commit=False),
    )
    assert runtime.is_canonical_ledger_authoritative

    Session = sessionmaker(bind=engine, expire_on_commit=False)
    ledger = PostgreSQLAtomicLedger(Session)

    for account_id, balance in (
        ("alice", 100),
        ("bob", 0),
        ("carol", 10),
        ("settlement-source", 50),
        ("settlement-destination", 0),
        ("smoke-release", 0),
        ("smoke-refund", 0),
        ("smoke-cancel", 0),
    ):
        ledger.create_account(account_id, "USD", balance)

    now = datetime.now(timezone.utc)
    with Session() as session:
        session.add_all(
            [
                CanonicalEscrow(
                    id="smoke-release",
                    sender_address="alice",
                    receiver_address="bob",
                    refund_destination="alice",
                    amount=30,
                    state=EscrowState.CREATED.value,
                    condition_desc="smoke",
                    currency="USD",
                    version=0,
                    created_at=now,
                    updated_at=now,
                ),
                CanonicalEscrow(
                    id="smoke-refund",
                    sender_address="alice",
                    receiver_address="bob",
                    refund_destination="alice",
                    amount=20,
                    state=EscrowState.CREATED.value,
                    condition_desc="smoke",
                    currency="USD",
                    version=0,
                    created_at=now,
                    updated_at=now,
                ),
                CanonicalEscrow(
                    id="smoke-cancel",
                    sender_address="carol",
                    receiver_address="bob",
                    refund_destination="carol",
                    amount=10,
                    state=EscrowState.CREATED.value,
                    condition_desc="smoke",
                    currency="USD",
                    version=0,
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        session.commit()

    with Session() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="smoke-fund-release",
            escrow_id="smoke-release",
            source="alice",
            amount=30,
            currency="USD",
        )
        session.commit()

    with Session() as session:
        lock_escrow_in_transaction(
            session,
            transaction_id="smoke-lock-release",
            escrow_id="smoke-release",
        )
        session.commit()

    with Session() as session:
        release_escrow_in_transaction(
            session,
            transaction_id="smoke-release-tx",
            escrow_id="smoke-release",
            beneficiary="bob",
            amount=30,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        session.commit()

    with Session() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="smoke-fund-refund",
            escrow_id="smoke-refund",
            source="alice",
            amount=20,
            currency="USD",
        )
        lock_escrow_in_transaction(
            session,
            transaction_id="smoke-lock-refund",
            escrow_id="smoke-refund",
        )
        refund_escrow_in_transaction(
            session,
            transaction_id="smoke-refund-tx",
            escrow_id="smoke-refund",
            amount=20,
            currency="USD",
        )
        session.commit()

    with Session() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="smoke-fund-cancel",
            escrow_id="smoke-cancel",
            source="carol",
            amount=10,
            currency="USD",
        )
        cancel_escrow_in_transaction(
            session,
            transaction_id="smoke-cancel-tx",
            escrow_id="smoke-cancel",
        )
        session.commit()

    with Session() as session:
        SettlementCoordinator(session).settle_in_transaction(
            transaction_id="smoke-settlement-tx",
            source="settlement-source",
            destination="settlement-destination",
            amount=20,
            currency="USD",
        )
        session.commit()

    with Session() as session:
        states = dict(
            session.execute(
                select(CanonicalEscrow.id, CanonicalEscrow.state)
            ).all()
        )
        assert states["smoke-release"] == EscrowState.RELEASED.value
        assert states["smoke-refund"] == EscrowState.REFUNDED.value
        assert states["smoke-cancel"] == EscrowState.CANCELLED.value

        balances = dict(
            session.execute(
                select(LedgerAccountModel.account_id, LedgerAccountModel.balance)
            ).all()
        )
        assert balances["alice"] == 70
        assert balances["bob"] == 30
        assert balances["carol"] == 10
        assert balances["settlement-source"] == 30
        assert balances["settlement-destination"] == 20

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()

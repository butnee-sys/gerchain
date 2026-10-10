from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from persistence.atomic_ledger import LedgerAccountModel
from persistence.cancel_escrow import cancel_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.settlement_coordinator import SettlementCoordinator
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


@pytest.mark.integration
def test_production_postgres_full_value_flow():
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_DATABASE_URL is required for PostgreSQL integration evidence")

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="it-esc-release",
            amount=40,
            currency="MNT",
            witness_id="it-witness",
        )
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)

    with factory.session_factory() as session:
        # Three independent escrows exercise RELEASE, REFUND, and CANCEL.
        accounts = [
            ("sender-release", 100),
            ("sender-refund", 100),
            ("sender-cancel", 100),
            ("beneficiary-release", 0),
            ("settlement-destination", 0),
            ("settlement-source", 50),
        ]
        for account_id, balance in accounts:
            runtime._canonical_ledger.create_account(
                account_id=account_id, currency="MNT", initial_balance=balance
            )

        for escrow_id, sender, receiver, refund_destination, amount in [
            ("it-esc-release", "sender-release", "beneficiary-release", "sender-release", 40),
            ("it-esc-refund", "sender-refund", "unused-beneficiary", "sender-refund", 30),
            ("it-esc-cancel", "sender-cancel", "unused-beneficiary-2", "sender-cancel", 20),
        ]:
            session.add(
                CanonicalEscrow(
                    id=escrow_id,
                    sender_address=sender,
                    receiver_address=receiver,
                    amount=Decimal(amount),
                    state=EscrowState.CREATED.value,
                    condition_desc="integration-test",
                    refund_destination=refund_destination,
                    currency="MNT",
                    version=0,
                    created_at=now,
                    updated_at=now,
                )
            )
        session.commit()

    with factory.session_factory() as session:
        fund_escrow_in_transaction(
            session, transaction_id="it-fund-release", escrow_id="it-esc-release",
            source="sender-release", amount=40, currency="MNT",
        )
        session.commit()
    with factory.session_factory() as session:
        lock_escrow_in_transaction(
            session, transaction_id="it-lock-release", escrow_id="it-esc-release",
        )
        session.commit()
    with factory.session_factory() as session:
        release_escrow_in_transaction(
            session, transaction_id="it-release", escrow_id="it-esc-release",
            beneficiary="beneficiary-release", amount=40, currency="MNT",
            decision_status="APPROVE", authorization_status="AUTHORIZED",
            trust=True, transparency=True, performance=True, evidence_verified=True,
        )
        session.commit()

    with factory.session_factory() as session:
        fund_escrow_in_transaction(
            session, transaction_id="it-fund-refund", escrow_id="it-esc-refund",
            source="sender-refund", amount=30, currency="MNT",
        )
        lock_escrow_in_transaction(
            session, transaction_id="it-lock-refund", escrow_id="it-esc-refund",
        )
        refund_escrow_in_transaction(
            session, transaction_id="it-refund", escrow_id="it-esc-refund",
            amount=30, currency="MNT",
        )
        session.commit()

    with factory.session_factory() as session:
        fund_escrow_in_transaction(
            session, transaction_id="it-fund-cancel", escrow_id="it-esc-cancel",
            source="sender-cancel", amount=20, currency="MNT",
        )
        cancel_escrow_in_transaction(
            session, transaction_id="it-cancel", escrow_id="it-esc-cancel",
        )
        SettlementCoordinator(session).settle_in_transaction(
            transaction_id="it-settlement", source="settlement-source",
            destination="settlement-destination", amount=10, currency="MNT",
        )
        session.commit()

    with factory.session_factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

        expected = {
            "sender-release": 60,
            "beneficiary-release": 40,
            "sender-refund": 100,
            "sender-cancel": 100,
            "settlement-source": 40,
            "settlement-destination": 10,
        }
        actual = {
            row.account_id: row.balance
            for row in session.execute(select(LedgerAccountModel)).scalars()
            if row.account_id in expected
        }
        assert actual == expected

        states = {
            row.id: row.state
            for row in session.execute(select(CanonicalEscrow)).scalars()
            if row.id.startswith("it-esc-")
        }
        assert states == {
            "it-esc-release": "RELEASED",
            "it-esc-refund": "REFUNDED",
            "it-esc-cancel": "CANCELLED",
        }

    factory.engine.dispose()

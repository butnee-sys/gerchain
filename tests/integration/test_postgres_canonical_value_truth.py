import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import select, text

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.cancel_escrow import cancel_escrow_in_transaction
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


DATABASE_URL = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL re-performance",
)


def _factory():
    return ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=DATABASE_URL,
            escrow_id="boot-escrow",
            amount=1,
            currency="USD",
            witness_id="boot-witness",
        )
    )


def _create_account(factory, account_id, balance):
    with factory.session_factory() as session:
        from persistence.atomic_ledger import PostgreSQLAtomicLedger

        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, account_id, "USD", balance
        )
        session.commit()


def _create_escrow(factory, escrow_id, sender, beneficiary, refund_destination, amount):
    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        session.add(
            CanonicalEscrow(
                id=escrow_id,
                sender_address=sender,
                receiver_address=beneficiary,
                refund_destination=refund_destination,
                amount=amount,
                currency="USD",
                state=EscrowState.CREATED.value,
                condition_desc="integration-test",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()


def test_postgres_boot_and_canonical_release_refund_cancel_truth():
    factory = _factory()
    with factory.engine.begin() as connection:
        connection.exec_driver_sql(
            "TRUNCATE TABLE gerchain_outbox_events, gerchain_transaction_witnesses, "
            "gerchain_idempotency_records, gerchain_ledger_movements, "
            "gerchain_ledger_accounts, escrows RESTART IDENTITY CASCADE"
        )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    _create_account(factory, "SRC-REL", 100)
    _create_account(factory, "ESC-REL", 0)
    _create_account(factory, "BEN-REL", 0)
    _create_escrow(factory, "ESC-REL", "SRC-REL", "BEN-REL", "SRC-REL", 40)

    with factory.session_factory() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="tx-fund-rel",
            escrow_id="ESC-REL",
            source="SRC-REL",
            amount=40,
            currency="USD",
        )
        lock_escrow_in_transaction(
            session,
            transaction_id="tx-lock-rel",
            escrow_id="ESC-REL",
        )
        release_escrow_in_transaction(
            session,
            transaction_id="tx-release-rel",
            escrow_id="ESC-REL",
            beneficiary="BEN-REL",
            amount=40,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        session.commit()

    _create_account(factory, "SRC-REF", 100)
    _create_account(factory, "ESC-REF", 0)
    _create_account(factory, "REF-DEST", 0)
    _create_escrow(factory, "ESC-REF", "SRC-REF", "BEN-REF", "REF-DEST", 25)

    with factory.session_factory() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="tx-fund-ref",
            escrow_id="ESC-REF",
            source="SRC-REF",
            amount=25,
            currency="USD",
        )
        lock_escrow_in_transaction(
            session,
            transaction_id="tx-lock-ref",
            escrow_id="ESC-REF",
        )
        refund_escrow_in_transaction(
            session,
            transaction_id="tx-refund-ref",
            escrow_id="ESC-REF",
            amount=25,
            currency="USD",
        )
        session.commit()

    _create_account(factory, "SRC-CAN", 100)
    _create_account(factory, "ESC-CAN", 0)
    _create_escrow(factory, "ESC-CAN", "SRC-CAN", "BEN-CAN", "SRC-CAN", 30)

    with factory.session_factory() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="tx-fund-can",
            escrow_id="ESC-CAN",
            source="SRC-CAN",
            amount=30,
            currency="USD",
        )
        cancel_escrow_in_transaction(
            session,
            transaction_id="tx-cancel-can",
            escrow_id="ESC-CAN",
        )
        session.commit()

    with factory.session_factory() as session:
        rows = {
            row.account_id: row.balance
            for row in session.execute(select(LedgerAccountModel)).scalars()
        }
        states = {
            row.id: row.state
            for row in session.execute(select(CanonicalEscrow)).scalars()
            if row.id in {"ESC-REL", "ESC-REF", "ESC-CAN"}
        }
        report = deep_reconcile_value_truth(session)

    assert rows["SRC-REL"] == 60
    assert rows["BEN-REL"] == 40
    assert rows["SRC-REF"] == 75
    assert rows["REF-DEST"] == 25
    assert rows["SRC-CAN"] == 100
    assert states == {
        "ESC-REL": "RELEASED",
        "ESC-REF": "REFUNDED",
        "ESC-CAN": "CANCELLED",
    }
    assert report.matched
    factory.engine.dispose()

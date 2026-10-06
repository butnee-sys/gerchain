from __future__ import annotations

import os
from datetime import datetime, timezone

from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)


def test_ea35_postgresql_production_path() -> None:
    database_url = os.environ["GERCHAIN_POSTGRES_TEST_URL"]

    config = ProductionRuntimeConfig(
        database_url=database_url,
        escrow_id="ea35-escrow",
        amount=100,
        currency="USD",
        witness_id="ea35-witness",
    )
    factory = ProductionRuntimeFactory(config)
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime._postgres_release is None

    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        runtime._canonical_ledger.create_account("ea35-source", "USD", 100)
        runtime._canonical_ledger.create_account("ea35-escrow", "USD", 0)
        runtime._canonical_ledger.create_account("ea35-beneficiary", "USD", 0)

        session.add(
            CanonicalEscrow(
                id="ea35-escrow",
                sender_address="ea35-source",
                receiver_address="ea35-beneficiary",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="EA-35 PostgreSQL production gate",
                refund_destination="ea35-source",
                currency="USD",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id="ea35-fund",
            escrow_id="ea35-escrow",
            source="ea35-source",
            amount=100,
            currency="USD",
        )
        session.commit()

        lock_escrow_in_transaction(
            session,
            transaction_id="ea35-lock",
            escrow_id="ea35-escrow",
        )
        session.commit()

        release_escrow_in_transaction(
            session,
            transaction_id="ea35-release",
            escrow_id="ea35-escrow",
            beneficiary="ea35-beneficiary",
            amount=100,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        session.commit()

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    with factory.session_factory() as session:
        source = runtime._canonical_read().get_balance("ea35-source", "USD")
        escrow = runtime._canonical_read().get_balance("ea35-escrow", "USD")
        beneficiary = runtime._canonical_read().get_balance("ea35-beneficiary", "USD")
        assert source["balance"] == 0
        assert escrow["balance"] == 0
        assert beneficiary["balance"] == 100

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.atomic_ledger import LedgerMovementModel
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


@pytest.mark.integration
def test_real_postgresql_canonical_runtime_and_value_truth():
    url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_DATABASE_URL is not configured")

    engine = create_engine(url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-ea35-escrow",
            amount=100,
            currency="USD",
            witness_id="pg-ea35-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        session.query(CanonicalEscrow).filter_by(id="pg-ea35-escrow").delete()
        session.query(LedgerMovementModel).filter(
            LedgerMovementModel.transaction_id.like("pg-ea35-%")
        ).delete(synchronize_session=False)
        session.query(LedgerAccountModel).filter(
            LedgerAccountModel.account_id.in_(["pg-source", "pg-ea35-escrow", "pg-beneficiary"])
        ).delete(synchronize_session=False)
        session.commit()

        session.add_all([
            LedgerAccountModel(account_id="pg-source", currency="USD", balance=100, version=0, updated_at=now),
            LedgerAccountModel(account_id="pg-ea35-escrow", currency="USD", balance=0, version=0, updated_at=now),
            LedgerAccountModel(account_id="pg-beneficiary", currency="USD", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="pg-ea35-escrow",
                sender_address="pg-source",
                receiver_address="pg-beneficiary",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="integration-test",
                refund_destination="pg-source",
                currency="USD",
                version=0,
                created_at=now,
                updated_at=now,
            ),
        ])
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id="pg-ea35-fund",
            escrow_id="pg-ea35-escrow",
            source="pg-source",
            amount=100,
            currency="USD",
            payload={"test": "fund"},
        )
        session.commit()

        lock_escrow_in_transaction(
            session,
            transaction_id="pg-ea35-lock",
            escrow_id="pg-ea35-escrow",
            payload={"test": "lock"},
        )
        session.commit()

        release_escrow_in_transaction(
            session,
            transaction_id="pg-ea35-release",
            escrow_id="pg-ea35-escrow",
            beneficiary="pg-beneficiary",
            amount=100,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
            payload={"test": "release"},
        )
        session.commit()

        source = session.get(LedgerAccountModel, "pg-source")
        escrow = session.get(LedgerAccountModel, "pg-ea35-escrow")
        beneficiary = session.get(LedgerAccountModel, "pg-beneficiary")
        assert source.balance == 0
        assert escrow.balance == 0
        assert beneficiary.balance == 100

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()

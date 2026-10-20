from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.atomic_ledger import LedgerAccountModel
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


pytestmark = pytest.mark.postgres


def test_production_postgresql_canonical_value_path():
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_DATABASE_URL is required")

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="pg-ea35-escrow",
            amount=100,
            currency="USD",
            witness_id="pg-ea35-witness",
        )
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        session.query(CanonicalEscrow).filter_by(id="pg-ea35-escrow").delete()
        session.query(LedgerAccountModel).filter(
            LedgerAccountModel.account_id.in_(["pg-source", "pg-ea35-escrow", "pg-beneficiary"])
        ).delete(synchronize_session=False)
        session.commit()

        session.add_all([
            LedgerAccountModel(
                account_id="pg-source",
                currency="USD",
                balance=100,
                version=0,
                updated_at=now,
            ),
            LedgerAccountModel(
                account_id="pg-ea35-escrow",
                currency="USD",
                balance=0,
                version=0,
                updated_at=now,
            ),
            LedgerAccountModel(
                account_id="pg-beneficiary",
                currency="USD",
                balance=0,
                version=0,
                updated_at=now,
            ),
            CanonicalEscrow(
                id="pg-ea35-escrow",
                sender_address="pg-source",
                receiver_address="pg-beneficiary",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="EA35 PostgreSQL proof",
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
            payload={"proof": "postgres"},
        )
        session.commit()

        lock_escrow_in_transaction(
            session,
            transaction_id="pg-ea35-lock",
            escrow_id="pg-ea35-escrow",
            payload={"proof": "postgres"},
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
            payload={"proof": "postgres"},
        )
        session.commit()

        escrow = session.get(CanonicalEscrow, "pg-ea35-escrow")
        source = session.get(LedgerAccountModel, "pg-source")
        beneficiary = session.get(LedgerAccountModel, "pg-beneficiary")

        assert escrow is not None
        assert escrow.state == EscrowState.RELEASED.value
        assert source is not None and source.balance == 0
        assert beneficiary is not None and beneficiary.balance == 100

        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}: {i.detail}" for i in report.issues]

    factory.engine.dispose()

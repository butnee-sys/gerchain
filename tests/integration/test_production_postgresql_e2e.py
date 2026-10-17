import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


pytestmark = pytest.mark.integration


def test_production_postgresql_boot_and_value_flow():
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_DATABASE_URL is required")

    config = ProductionRuntimeConfig(
        database_url=database_url,
        escrow_id="pg-e2e-escrow",
        amount=40,
        currency="MNT",
        witness_id="pg-e2e-witness",
    )
    factory = ProductionRuntimeFactory(config)
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    Session = sessionmaker(bind=factory.engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    with Session() as session:
        session.execute(text("DELETE FROM gerchain_idempotency_records"))
        session.execute(text("DELETE FROM gerchain_outbox_events"))
        session.execute(text("DELETE FROM gerchain_transaction_witnesses"))
        session.execute(text("DELETE FROM gerchain_ledger_movements"))
        session.execute(text("DELETE FROM gerchain_ledger_accounts"))
        session.execute(text("DELETE FROM escrows"))

        session.add_all([
            LedgerAccountModel(
                account_id="pg-source",
                currency="MNT",
                balance=100,
                version=0,
                updated_at=now,
            ),
            LedgerAccountModel(
                account_id="pg-e2e-escrow",
                currency="MNT",
                balance=0,
                version=0,
                updated_at=now,
            ),
            LedgerAccountModel(
                account_id="pg-beneficiary",
                currency="MNT",
                balance=0,
                version=0,
                updated_at=now,
            ),
        ])
        session.add(
            CanonicalEscrow(
                id="pg-e2e-escrow",
                sender_address="pg-source",
                receiver_address="pg-beneficiary",
                amount=40,
                state=EscrowState.CREATED.value,
                condition_desc="production-e2e",
                refund_destination="pg-source",
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-1",
            escrow_id="pg-e2e-escrow",
            source="pg-source",
            amount=40,
            currency="MNT",
        )
        session.commit()

        lock_escrow_in_transaction(
            session,
            transaction_id="pg-lock-1",
            escrow_id="pg-e2e-escrow",
        )
        session.commit()

        release_escrow_in_transaction(
            session,
            transaction_id="pg-release-1",
            escrow_id="pg-e2e-escrow",
            beneficiary="pg-beneficiary",
            amount=40,
            currency="MNT",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        session.commit()

        source = session.execute(
            select(LedgerAccountModel).where(LedgerAccountModel.account_id == "pg-source")
        ).scalar_one()
        beneficiary = session.execute(
            select(LedgerAccountModel).where(LedgerAccountModel.account_id == "pg-beneficiary")
        ).scalar_one()
        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "pg-e2e-escrow")
        ).scalar_one()

        assert source.balance == 60
        assert beneficiary.balance == 40
        assert escrow.state == EscrowState.RELEASED.value

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    factory.engine.dispose()

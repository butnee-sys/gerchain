import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from persistence.atomic_ledger import LedgerAccountModel, PostgreSQLAtomicLedger
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


@pytest.mark.integration
def test_production_postgres_full_value_flow():
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_DATABASE_URL is required")

    config = ProductionRuntimeConfig(
        database_url=database_url,
        escrow_id="integration-escrow-1",
        amount=40,
        currency="USD",
        witness_id="integration-witness-1",
    )
    factory = ProductionRuntimeFactory(config)
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    with factory.session_factory() as session:
        # Clean only the deterministic integration aggregate.
        session.query(CanonicalEscrow).filter(CanonicalEscrow.id == config.escrow_id).delete()
        session.query(LedgerAccountModel).filter(
            LedgerAccountModel.account_id.in_(["integration-source", config.escrow_id, "integration-beneficiary"])
        ).delete(synchronize_session=False)
        session.commit()

        ledger = PostgreSQLAtomicLedger(factory.session_factory)
        ledger.create_account("integration-source", "USD", 100)
        ledger.create_account(config.escrow_id, "USD", 0)
        ledger.create_account("integration-beneficiary", "USD", 0)

        now = datetime.now(timezone.utc)
        with factory.session_factory() as tx:
            tx.add(CanonicalEscrow(
                id=config.escrow_id,
                sender_address="integration-source",
                receiver_address="integration-beneficiary",
                refund_destination="integration-source",
                amount=40,
                state=EscrowState.CREATED.value,
                condition_desc="integration",
                currency="USD",
                version=0,
                created_at=now,
                updated_at=now,
            ))
            tx.commit()

        with factory.session_factory() as tx:
            fund_escrow_in_transaction(
                tx,
                transaction_id="integration-fund-1",
                escrow_id=config.escrow_id,
                source="integration-source",
                amount=40,
                currency="USD",
            )
            tx.commit()

        with factory.session_factory() as tx:
            lock_escrow_in_transaction(
                tx,
                transaction_id="integration-lock-1",
                escrow_id=config.escrow_id,
            )
            tx.commit()

        with factory.session_factory() as tx:
            release_escrow_in_transaction(
                tx,
                transaction_id="integration-release-1",
                escrow_id=config.escrow_id,
                beneficiary="integration-beneficiary",
                amount=40,
                currency="USD",
                decision_status="APPROVE",
                authorization_status="AUTHORIZED",
                trust=True,
                transparency=True,
                performance=True,
                evidence_verified=True,
            )
            tx.commit()

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == config.escrow_id)
        ).scalar_one()
        assert escrow.state == EscrowState.RELEASED.value

        balances = {
            row.account_id: row.balance
            for row in session.execute(
                select(LedgerAccountModel).where(
                    LedgerAccountModel.account_id.in_(
                        ["integration-source", config.escrow_id, "integration-beneficiary"]
                    )
                )
            ).scalars()
        }
        assert balances == {
            "integration-source": 60,
            config.escrow_id: 0,
            "integration-beneficiary": 40,
        }

    factory.engine.dispose()

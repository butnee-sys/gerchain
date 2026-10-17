from datetime import datetime, timezone

from persistence.atomic_ledger import LedgerAccountModel, PostgreSQLAtomicLedger
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.release_escrow import release_escrow_in_transaction
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_real_postgresql_canonical_value_flow():
    import os

    url = os.environ["GERCHAIN_DATABASE_URL"]
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-e2e-escrow",
            amount=40,
            currency="USD",
            witness_id="pg-e2e-witness",
        )
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, "PG-SOURCE", "USD", 100
        )
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, "pg-e2e-escrow", "USD", 0
        )
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, "PG-BENEFICIARY", "USD", 0
        )
        session.add(
            CanonicalEscrow(
                id="pg-e2e-escrow",
                sender_address="PG-SOURCE",
                receiver_address="PG-BENEFICIARY",
                refund_destination="PG-SOURCE",
                amount=40,
                state=EscrowState.CREATED.value,
                condition_desc="production-e2e",
                currency="USD",
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
            source="PG-SOURCE",
            amount=40,
            currency="USD",
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
            beneficiary="PG-BENEFICIARY",
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

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

        balances = {
            row.account_id: row.balance
            for row in session.query(LedgerAccountModel).all()
        }
        assert balances["PG-SOURCE"] == 60
        assert balances["pg-e2e-escrow"] == 0
        assert balances["PG-BENEFICIARY"] == 40

        escrow = session.get(CanonicalEscrow, "pg-e2e-escrow")
        assert escrow is not None
        assert escrow.state == EscrowState.RELEASED.value

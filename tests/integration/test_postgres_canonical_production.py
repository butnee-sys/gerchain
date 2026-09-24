import os
from datetime import datetime, timezone
from sqlalchemy import select
from persistence.atomic_ledger import LedgerAccountModel, PostgreSQLAtomicLedger
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory

def test_postgres_canonical_production_flow():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    escrow_id, source, beneficiary, currency, amount = "ci-escrow-1", "ci-source", "ci-beneficiary", "USD", 100
    factory = ProductionRuntimeFactory(ProductionRuntimeConfig(url, escrow_id, amount, currency, "ci-witness"))
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative
    with factory.session_factory() as session:
        for account_id, balance in ((source, 100), (escrow_id, 0), (beneficiary, 0)):
            PostgreSQLAtomicLedger.create_account_in_transaction(session, account_id, currency, balance)
        now = datetime.now(timezone.utc)
        session.add(CanonicalEscrow(
            id=escrow_id, sender_address=source, receiver_address=beneficiary,
            refund_destination=source, amount=amount, state=EscrowState.CREATED.value,
            condition_desc="CI production proof", currency=currency, version=0,
            created_at=now, updated_at=now))
        session.commit()
        fund_escrow_in_transaction(session, transaction_id="ci-fund-1", escrow_id=escrow_id, source=source, amount=amount, currency=currency)
        session.commit()
        lock_escrow_in_transaction(session, transaction_id="ci-lock-1", escrow_id=escrow_id)
        session.commit()
        release_escrow_in_transaction(
            session, transaction_id="ci-release-1", escrow_id=escrow_id,
            beneficiary=beneficiary, amount=amount, currency=currency,
            decision_status="APPROVE", authorization_status="AUTHORIZED",
            trust=True, transparency=True, performance=True, evidence_verified=True)
        session.commit()
        escrow = session.execute(select(CanonicalEscrow).where(CanonicalEscrow.id == escrow_id)).scalar_one()
        assert escrow.state == EscrowState.RELEASED.value
        assert session.get(LedgerAccountModel, source).balance == 0
        assert session.get(LedgerAccountModel, beneficiary).balance == 100
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

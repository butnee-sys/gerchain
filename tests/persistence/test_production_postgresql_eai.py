import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_postgresql_canonical_value_flow():
    database_url = os.environ["GERCHAIN_POSTGRES_DSN"]
    engine = create_engine(database_url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="eai-proof-1",
            amount=10,
            currency="USD",
            witness_id="witness-eai-proof-1",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    Session = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)
    with Session() as session:
        session.add_all([
            CanonicalEscrow(
                id="eai-proof-1",
                sender_address="SRC",
                receiver_address="DST",
                amount=10,
                state=EscrowState.CREATED.value,
                condition_desc="production proof",
                refund_destination="SRC",
                currency="USD",
                version=0,
                created_at=now,
                updated_at=now,
            ),
        ])
        from persistence.atomic_ledger import PostgreSQLAtomicLedger
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "SRC", "USD", 100)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "eai-proof-1", "USD", 0)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "DST", "USD", 0)
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id="eai-fund-1",
            escrow_id="eai-proof-1",
            source="SRC",
            amount=10,
            currency="USD",
        )
        session.commit()

        lock_escrow_in_transaction(
            session,
            transaction_id="eai-lock-1",
            escrow_id="eai-proof-1",
        )
        session.commit()

        release_escrow_in_transaction(
            session,
            transaction_id="eai-release-1",
            escrow_id="eai-proof-1",
            beneficiary="DST",
            amount=10,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        session.commit()

        escrow = session.get(CanonicalEscrow, "eai-proof-1")
        assert escrow.state == EscrowState.RELEASED.value
        assert session.get(LedgerAccountModel, "SRC").balance == 90
        assert session.get(LedgerAccountModel, "DST").balance == 10
        assert session.get(LedgerAccountModel, "eai-proof-1").balance == 0

        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}:{i.transaction_id}:{i.detail}" for i in report.issues]

    engine.dispose()

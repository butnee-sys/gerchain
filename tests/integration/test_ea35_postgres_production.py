import os
from datetime import datetime, timezone

from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import ProductionRuntimeFactory
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.atomic_ledger import PostgreSQLAtomicLedger, LedgerAccountModel
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth


def test_production_postgres_fund_lock_release_reconciles():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    runtime = ProductionRuntimeFactory.create(
        escrow_id="pg-ea35-escrow",
        amount=100,
        currency="USD",
        witness_id="pg-ea35-witness",
        engine=engine,
        session_factory=factory,
    )
    with factory() as session:
        ledger = PostgreSQLAtomicLedger(factory)
        ledger.create_account("pg-source", "USD", initial_balance=100)
        ledger.create_account("pg-beneficiary", "USD", initial_balance=0)
        session.add(CanonicalEscrow(
            id="pg-ea35-escrow",
            sender_address="pg-source",
            receiver_address="pg-beneficiary",
            amount=100,
            state=EscrowState.CREATED.value,
            condition_desc="production integration",
            refund_destination="pg-source",
            currency="USD",
            version=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ))
        session.commit()

    with factory() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-1",
            escrow_id="pg-ea35-escrow",
            source="pg-source",
            amount=100,
            currency="USD",
        )
        session.commit()

    with factory() as session:
        lock_escrow_in_transaction(
            session,
            transaction_id="pg-lock-1",
            escrow_id="pg-ea35-escrow",
        )
        session.commit()

    with factory() as session:
        release_escrow_in_transaction(
            session,
            transaction_id="pg-release-1",
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
        )
        session.commit()

    with factory() as session:
        balances = {
            row.account_id: row.balance
            for row in session.execute(select(LedgerAccountModel)).scalars()
        }
        escrow = session.get(CanonicalEscrow, "pg-ea35-escrow")
        report = deep_reconcile_value_truth(session)
        assert balances["pg-source"] == 0
        assert balances["pg-beneficiary"] == 100
        assert escrow.state == EscrowState.RELEASED.value
        assert report.matched, [f"{i.code}: {i.detail}" for i in report.issues]

    engine.dispose()

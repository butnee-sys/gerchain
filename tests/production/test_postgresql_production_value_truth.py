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


def test_postgresql_production_value_truth_roundtrip():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-smoke-escrow",
            amount=100,
            currency="MNT",
            witness_id="pg-smoke-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    Session = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    with Session() as session:
        for account_id, balance in (("pg-source", 100), ("pg-smoke-escrow", 0), ("pg-beneficiary", 0)):
            session.merge(LedgerAccountModel(
                account_id=account_id,
                currency="MNT",
                balance=balance,
                version=0,
                updated_at=now,
            ))
        session.add(CanonicalEscrow(
            id="pg-smoke-escrow",
            sender_address="pg-source",
            receiver_address="pg-beneficiary",
            amount=100,
            state=EscrowState.CREATED.value,
            condition_desc="production-postgresql-smoke",
            refund_destination="pg-source",
            currency="MNT",
            version=0,
            created_at=now,
            updated_at=now,
        ))
        session.commit()

    with Session() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-1",
            escrow_id="pg-smoke-escrow",
            source="pg-source",
            amount=100,
            currency="MNT",
        )
        session.commit()

    with Session() as session:
        lock_escrow_in_transaction(
            session,
            transaction_id="pg-lock-1",
            escrow_id="pg-smoke-escrow",
        )
        session.commit()

    with Session() as session:
        release_escrow_in_transaction(
            session,
            transaction_id="pg-release-1",
            escrow_id="pg-smoke-escrow",
            beneficiary="pg-beneficiary",
            amount=100,
            currency="MNT",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        session.commit()

    with Session() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues
        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "pg-smoke-escrow")
        ).scalar_one()
        source = session.get(LedgerAccountModel, "pg-source")
        beneficiary = session.get(LedgerAccountModel, "pg-beneficiary")
        assert escrow.state == EscrowState.RELEASED.value
        assert source.balance == 0
        assert beneficiary.balance == 100

    engine.dispose()

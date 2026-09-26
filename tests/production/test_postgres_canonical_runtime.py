import os
from datetime import datetime, timezone

from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_postgres_canonical_fund_lock_release_reconciles():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-proof-escrow",
            amount=100,
            currency="MNT",
            witness_id="pg-proof-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    Session = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    with Session() as session:
        for account_id, balance in (("pg-proof-source", 200), ("pg-proof-escrow", 0), ("pg-proof-beneficiary", 0)):
            session.add(LedgerAccountModel(
                account_id=account_id,
                currency="MNT",
                balance=balance,
                version=0,
                updated_at=now,
            ))
        session.add(CanonicalEscrow(
            id="pg-proof-escrow",
            sender_address="pg-proof-source",
            receiver_address="pg-proof-beneficiary",
            refund_destination="pg-proof-source",
            amount=100,
            state="CREATED",
            condition_desc="production proof",
            currency="MNT",
            version=0,
            created_at=now,
            updated_at=now,
        ))
        session.commit()

    with Session() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="pg-proof-fund",
            escrow_id="pg-proof-escrow",
            source="pg-proof-source",
            amount=100,
            currency="MNT",
        )
        session.commit()

    with Session() as session:
        lock_escrow_in_transaction(
            session,
            transaction_id="pg-proof-lock",
            escrow_id="pg-proof-escrow",
        )
        session.commit()

    with Session() as session:
        release_escrow_in_transaction(
            session,
            transaction_id="pg-proof-release",
            escrow_id="pg-proof-escrow",
            beneficiary="pg-proof-beneficiary",
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
        escrow = session.get(CanonicalEscrow, "pg-proof-escrow")
        source = session.get(LedgerAccountModel, "pg-proof-source")
        beneficiary = session.get(LedgerAccountModel, "pg-proof-beneficiary")
        report = deep_reconcile_value_truth(session)

        assert escrow.state == "RELEASED"
        assert source.balance == 100
        assert beneficiary.balance == 100
        assert report.matched, report.issues
        assert report.canonical_movement_count == 2
        assert report.witness_count == 3
        assert report.outbox_count == 3

    engine.dispose()

# EA-35.13: executed through the pull-request PostgreSQL proof gate.

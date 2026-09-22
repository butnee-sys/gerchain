import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.atomic_value_transaction import TransactionWitness
from persistence.recovery_outbox import OutboxEvent
from persistence.durable_idempotency import DurableIdempotencyRecord
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_postgresql_canonical_runtime_end_to_end():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    runtime = ProductionRuntimeFactory(ProductionRuntimeConfig(
        database_url=url, escrow_id="pg-e2e-escrow", amount=40,
        currency="MNT", witness_id="pg-e2e-witness"), engine=engine).create()
    assert runtime.is_canonical_ledger_authoritative

    with factory() as session:
        now = datetime.now(timezone.utc)
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
            CanonicalEscrow(
                id="pg-e2e-escrow",
                sender_address="pg-source",
                receiver_address="pg-beneficiary",
                refund_destination="pg-source",
                amount=40,
                state="CREATED",
                condition_desc="integration-test",
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            ),
        ])
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

        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "pg-e2e-escrow")
        ).scalar_one()
        source = session.get(LedgerAccountModel, "pg-source")
        beneficiary = session.get(LedgerAccountModel, "pg-beneficiary")

        assert escrow.state == "RELEASED"
        assert int(source.balance) == 60
        assert int(beneficiary.balance) == 40
        assert session.execute(select(TransactionWitness)).scalars().all()
        assert session.execute(select(OutboxEvent)).scalars().all()
        assert session.execute(select(DurableIdempotencyRecord)).scalars().all()

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()

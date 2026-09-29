import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.atomic_value_transaction import TransactionWitness
from persistence.durable_idempotency import DurableIdempotencyRecord
from persistence.escrow_aggregate import CanonicalEscrow
from persistence.recovery_outbox import OutboxEvent
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_postgresql_boot_and_canonical_value_flow():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="escrow-integration-1",
            amount=100,
            currency="USD",
            witness_id="witness-integration-1",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        now = datetime.now(timezone.utc)
        session.add_all([
            LedgerAccountModel(account_id="source-integration", currency="USD", balance=100, version=0, updated_at=now),
            LedgerAccountModel(account_id="beneficiary-integration", currency="USD", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="escrow-integration-1",
                sender_address="source-integration",
                receiver_address="beneficiary-integration",
                amount=100,
                state="CREATED",
                condition_desc="integration",
                refund_destination="source-integration",
                currency="USD",
                version=0,
                created_at=now,
                updated_at=now,
            ),
        ])
        session.commit()

    assert runtime.fund("fund-integration-1", "source-integration", "T1", {"verified": True})["replayed"] is False
    assert runtime.lock("lock-integration-1", "T2", {"verified": True})["replayed"] is False

    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        escrow = session.get(CanonicalEscrow, "escrow-integration-1")
        assert escrow.state == "LOCKED"

    # Release boundary is tested directly so the integration test does not
    # manufacture a DEE root-of-trust object merely for persistence testing.
    from persistence.release_escrow import release_escrow_in_transaction

    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        result = release_escrow_in_transaction(
            session,
            transaction_id="release-integration-1",
            escrow_id="escrow-integration-1",
            beneficiary="beneficiary-integration",
            amount=100,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
            payload={"integration": True},
        )
        session.commit()
        assert result["replayed"] is False

        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}:{i.transaction_id}:{i.detail}" for i in report.issues]

        source = session.get(LedgerAccountModel, "source-integration")
        escrow_account = session.get(LedgerAccountModel, "escrow-integration-1")
        beneficiary = session.get(LedgerAccountModel, "beneficiary-integration")
        durable_escrow = session.get(CanonicalEscrow, "escrow-integration-1")
        assert (source.balance, escrow_account.balance, beneficiary.balance) == (0, 0, 100)
        assert durable_escrow is not None and durable_escrow.state == "RELEASED"
        assert session.execute(select(TransactionWitness)).scalars().all()
        assert session.execute(select(OutboxEvent)).scalars().all()
        assert session.execute(select(DurableIdempotencyRecord)).scalars().all()

    engine.dispose()

from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import select

from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.atomic_ledger import LedgerAccountModel
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.atomic_value_transaction import TransactionWitness
from persistence.recovery_outbox import OutboxEvent
from persistence.durable_idempotency import DurableIdempotencyRecord
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_postgresql_boot_and_value_truth() -> None:
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    config = ProductionRuntimeConfig(
        database_url=database_url,
        escrow_id="pg-e2e-escrow",
        amount=100,
        currency="USD",
        witness_id="pg-e2e-witness",
    )
    factory = ProductionRuntimeFactory(config)
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        session.add_all(
            [
                LedgerAccountModel(
                    account_id="pg-source",
                    currency="USD",
                    balance=100,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="pg-beneficiary",
                    currency="USD",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
                CanonicalEscrow(
                    id="pg-e2e-escrow",
                    sender_address="pg-source",
                    receiver_address="pg-beneficiary",
                    amount=100,
                    state=EscrowState.CREATED.value,
                    condition_desc="production postgres e2e",
                    refund_destination="pg-source",
                    currency="USD",
                    version=0,
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        session.commit()

    with factory.session_factory() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-1",
            escrow_id="pg-e2e-escrow",
            source="pg-source",
            amount=100,
            currency="USD",
        )
        session.commit()

    with factory.session_factory() as session:
        lock_escrow_in_transaction(
            session,
            transaction_id="pg-lock-1",
            escrow_id="pg-e2e-escrow",
        )
        session.commit()

    with factory.session_factory() as session:
        release_escrow_in_transaction(
            session,
            transaction_id="pg-release-1",
            escrow_id="pg-e2e-escrow",
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

    with factory.session_factory() as session:
        source = session.execute(
            select(LedgerAccountModel).where(LedgerAccountModel.account_id == "pg-source")
        ).scalar_one()
        beneficiary = session.execute(
            select(LedgerAccountModel).where(LedgerAccountModel.account_id == "pg-beneficiary")
        ).scalar_one()
        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "pg-e2e-escrow")
        ).scalar_one()

        assert source.balance == 0
        assert beneficiary.balance == 100
        assert escrow.state == EscrowState.RELEASED.value

        assert session.execute(select(TransactionWitness)).scalars().all()
        assert session.execute(select(OutboxEvent)).scalars().all()
        assert session.execute(select(DurableIdempotencyRecord)).scalars().all()

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    factory.engine.dispose()

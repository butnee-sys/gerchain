from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.atomic_value_transaction import TransactionWitness
from persistence.recovery_outbox import OutboxEvent
from persistence.durable_idempotency import DurableIdempotencyRecord


def test_production_factory_boots_against_postgresql():
    database_url = os.environ["GERCHAIN_TEST_DATABASE_URL"]
    engine = create_engine(database_url, pool_pre_ping=True)

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="pg-boot-escrow",
            amount=100,
            currency="MNT",
            witness_id="pg-boot-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    Session = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    with Session() as session:
        session.add_all(
            [
                LedgerAccountModel(
                    account_id="PG-SRC",
                    currency="MNT",
                    balance=1000,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="pg-boot-escrow",
                    currency="MNT",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="PG-DST",
                    currency="MNT",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
            ]
        )
        session.add(
            CanonicalEscrow(
                id="pg-boot-escrow",
                sender_address="PG-SRC",
                receiver_address="PG-DST",
                refund_destination="PG-SRC",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="production boot proof",
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    with Session() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-1",
            escrow_id="pg-boot-escrow",
            source="PG-SRC",
            amount=100,
            currency="MNT",
        )
        session.commit()

    with Session() as session:
        lock_escrow_in_transaction(
            session,
            transaction_id="pg-lock-1",
            escrow_id="pg-boot-escrow",
        )
        session.commit()

    with Session() as session:
        release_escrow_in_transaction(
            session,
            transaction_id="pg-release-1",
            escrow_id="pg-boot-escrow",
            beneficiary="PG-DST",
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
        src = session.execute(
            select(LedgerAccountModel).where(LedgerAccountModel.account_id == "PG-SRC")
        ).scalar_one()
        dst = session.execute(
            select(LedgerAccountModel).where(LedgerAccountModel.account_id == "PG-DST")
        ).scalar_one()
        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "pg-boot-escrow")
        ).scalar_one()
        assert src.balance == 900
        assert dst.balance == 100
        assert escrow.state == EscrowState.RELEASED.value
        assert session.execute(select(TransactionWitness)).scalars().all()
        assert session.execute(select(OutboxEvent)).scalars().all()
        assert session.execute(select(DurableIdempotencyRecord)).scalars().all()
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()

# PostgreSQL production verification gate: exercised in CI with a real PostgreSQL service.

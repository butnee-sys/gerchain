from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState, EscrowBase
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.recovery_outbox import OutboxBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.atomic_value_transaction import WitnessBase
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_postgresql_production_reperformance():
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    suffix = uuid.uuid4().hex[:12]
    escrow_id = f"eai-{suffix}"
    source = f"source-{suffix}"
    beneficiary = f"beneficiary-{suffix}"
    witness_id = f"witness-{suffix}"
    amount = 100
    currency = "USD"

    engine = create_engine(database_url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id=escrow_id,
            amount=amount,
            currency=currency,
            witness_id=witness_id,
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        PostgreSQL = __import__(
            "persistence.atomic_ledger",
            fromlist=["PostgreSQLAtomicLedger"],
        ).PostgreSQLAtomicLedger
        PostgreSQL.create_account_in_transaction(session, source, currency, amount)
        PostgreSQL.create_account_in_transaction(session, escrow_id, currency, 0)
        PostgreSQL.create_account_in_transaction(session, beneficiary, currency, 0)
        now = datetime.now(timezone.utc)
        session.add(
            CanonicalEscrow(
                id=escrow_id,
                sender_address=source,
                receiver_address=beneficiary,
                refund_destination=source,
                amount=amount,
                currency=currency,
                state=EscrowState.CREATED.value,
                condition_desc="production-reperformance",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id=f"fund-{suffix}",
            escrow_id=escrow_id,
            source=source,
            amount=amount,
            currency=currency,
        )
        session.commit()

        lock_escrow_in_transaction(
            session,
            transaction_id=f"lock-{suffix}",
            escrow_id=escrow_id,
        )
        session.commit()

        release_escrow_in_transaction(
            session,
            transaction_id=f"release-{suffix}",
            escrow_id=escrow_id,
            beneficiary=beneficiary,
            amount=amount,
            currency=currency,
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        session.commit()

        balances = dict(
            session.execute(
                select(LedgerAccountModel.account_id, LedgerAccountModel.balance)
                .where(
                    LedgerAccountModel.account_id.in_(
                        [source, escrow_id, beneficiary]
                    )
                )
            ).all()
        )
        assert balances == {source: 0, escrow_id: 0, beneficiary: amount}

        escrow = session.get(CanonicalEscrow, escrow_id)
        assert escrow is not None
        assert escrow.state == EscrowState.RELEASED.value

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()

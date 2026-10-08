from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import delete

from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import DurableIdempotencyRecord
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxEvent
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory

pytestmark = pytest.mark.postgres


def test_production_postgresql_boot_fund_lock_release_and_reconcile():
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_DATABASE_URL is not configured")
    if not database_url.startswith("postgresql"):
        pytest.fail("GERCHAIN_DATABASE_URL must point to PostgreSQL")

    suffix = uuid4().hex
    escrow_id = f"eai-pg-{suffix}"
    source = f"source-{suffix}"
    beneficiary = f"beneficiary-{suffix}"
    witness_id = f"witness-{suffix}"
    amount = 10
    currency = "USD"

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id=escrow_id,
            amount=amount,
            currency=currency,
            witness_id=witness_id,
        )
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative
    now = datetime.now(timezone.utc)

    try:
        with factory.session_factory() as session:
            session.add_all([
                LedgerAccountModel(account_id=source, currency=currency, balance=100, version=0, updated_at=now),
                LedgerAccountModel(account_id=escrow_id, currency=currency, balance=0, version=0, updated_at=now),
                LedgerAccountModel(account_id=beneficiary, currency=currency, balance=0, version=0, updated_at=now),
                CanonicalEscrow(
                    id=escrow_id, sender_address=source, receiver_address=beneficiary,
                    amount=amount, state=EscrowState.CREATED.value,
                    condition_desc="production-postgresql-proof", refund_destination=source,
                    currency=currency, version=0, created_at=now, updated_at=now,
                ),
            ])
            session.commit()

        runtime.fund("pg-fund-" + suffix, source, now.isoformat(), {"test": "postgres"})
        runtime.lock("pg-lock-" + suffix, now.isoformat(), {"test": "postgres"})
        runtime.release(
            transaction_id="pg-release-" + suffix,
            destination=beneficiary, timestamp=now.isoformat(),
            evidence={"test": "postgres"}, root=object(), owner_id="postgres-proof",
            authorized=True, evidence_verified=True,
            trinity_proof={"trust": True, "transparency": True, "performance": True},
        )

        assert runtime.get_balance(source) == 90
        assert runtime.get_balance(escrow_id) == 0
        assert runtime.get_balance(beneficiary) == 10
        assert runtime.get_escrow_state()["state"] == EscrowState.RELEASED.value

        with factory.session_factory() as session:
            report = deep_reconcile_value_truth(session)
            assert report.matched, [f"{i.code}:{i.detail}" for i in report.issues]
    finally:
        with factory.session_factory() as session:
            session.execute(\n                delete(LedgerMovementModel).where(\n                    LedgerMovementModel.transaction_id.in_([\n                        "pg-fund-" + suffix,\n                        "pg-release-" + suffix,\n                    ])\n                )\n            )\n            session.execute(\n                delete(TransactionWitness).where(TransactionWitness.escrow_id == escrow_id)\n            )\n            session.execute(\n                delete(OutboxEvent).where(OutboxEvent.aggregate_id == escrow_id)\n            )
            session.execute(delete(DurableIdempotencyRecord).where(
                DurableIdempotencyRecord.key.in_([
                    "pg-fund-" + suffix, "pg-lock-" + suffix, "pg-release-" + suffix,
                ])
            ))
            session.execute(delete(CanonicalEscrow).where(CanonicalEscrow.id == escrow_id))
            session.execute(delete(LedgerAccountModel).where(
                LedgerAccountModel.account_id.in_([source, escrow_id, beneficiary])
            ))
            session.commit()
        factory.engine.dispose()

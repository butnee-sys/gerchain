from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.atomic_ledger import LedgerAccountModel
from persistence.atomic_value_transaction import TransactionWitness
from persistence.recovery_outbox import OutboxEvent
from persistence.durable_idempotency import DurableIdempotencyRecord
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


@pytest.fixture()
def production_runtime():
    dsn = os.environ.get("GERCHAIN_POSTGRES_DSN")
    if not dsn:
        pytest.skip("GERCHAIN_POSTGRES_DSN is required")
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=dsn,
            escrow_id="eai-pg-proof",
            amount=100,
            currency="USD",
            witness_id="witness-pg-proof",
        )
    )
    runtime = factory.create()
    yield runtime, factory
    factory.engine.dispose()


def test_production_factory_establishes_canonical_authority(production_runtime):
    runtime, _ = production_runtime
    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"


def test_postgresql_canonical_fund_lock_release_proof(production_runtime):
    runtime, factory = production_runtime
    sf = factory.session_factory
    now = datetime.now(timezone.utc)

    with sf() as session:
        session.add_all([
            LedgerAccountModel(account_id="pg-source", currency="USD", balance=100, version=0, updated_at=now),
            LedgerAccountModel(account_id="eai-pg-proof", currency="USD", balance=0, version=0, updated_at=now),
            LedgerAccountModel(account_id="pg-beneficiary", currency="USD", balance=0, version=0, updated_at=now),
            CanonicalEscrow(
                id="eai-pg-proof",
                sender_address="pg-source",
                receiver_address="pg-beneficiary",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="production proof",
                refund_destination="pg-source",
                currency="USD",
                version=0,
                created_at=now,
                updated_at=now,
            ),
        ])
        session.commit()

    with sf() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="pg-fund-1",
            escrow_id="eai-pg-proof",
            source="pg-source",
            amount=100,
            currency="USD",
            payload={"proof": "production"},
        )
        session.commit()

    with sf() as session:
        lock_escrow_in_transaction(
            session,
            transaction_id="pg-lock-1",
            escrow_id="eai-pg-proof",
            payload={"proof": "production"},
        )
        session.commit()

    with sf() as session:
        release_escrow_in_transaction(
            session,
            transaction_id="pg-release-1",
            escrow_id="eai-pg-proof",
            beneficiary="pg-beneficiary",
            amount=100,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
            payload={"proof": "production"},
        )
        session.commit()

    with sf() as session:
        escrow = session.get(CanonicalEscrow, "eai-pg-proof")
        source = session.get(LedgerAccountModel, "pg-source")
        beneficiary = session.get(LedgerAccountModel, "pg-beneficiary")
        movement = session.execute(select(__import__("persistence.atomic_ledger", fromlist=["LedgerMovementModel"]).LedgerMovementModel).where(__import__("persistence.atomic_ledger", fromlist=["LedgerMovementModel"]).LedgerMovementModel.transaction_id == "pg-release-1")).scalar_one()
        witness = session.execute(select(TransactionWitness).where(TransactionWitness.transaction_id == "pg-release-1")).scalar_one()
        outbox = session.execute(select(OutboxEvent).where(OutboxEvent.event_id == "gerchain_released:pg-release-1")).scalar_one()
        idem = session.execute(select(DurableIdempotencyRecord).where(DurableIdempotencyRecord.key == "pg-release-1")).scalar_one()

        assert runtime.is_canonical_ledger_authoritative
        assert escrow.state == EscrowState.RELEASED.value
        assert source.balance == 0
        assert beneficiary.balance == 100
        assert movement.operation == "RELEASE"
        assert movement.escrow_id == "eai-pg-proof"
        assert len(movement.integrity_hash) == 64
        assert witness.event_type == "GERCHAIN_RELEASED"
        assert outbox.aggregate_id == "eai-pg-proof"
        assert outbox.event_type == "GERCHAIN_RELEASED"
        assert idem.state == "COMPLETED"

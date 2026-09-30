from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import TransactionWitness
from persistence.durable_idempotency import IdempotencyBase
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowBase
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.recovery_outbox import OutboxBase
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


pytestmark = pytest.mark.integration


def _database_url() -> str:
    value = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
    if not value:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is not configured")
    return value


def test_postgresql_production_runtime_boot_and_value_flow() -> None:
    url = _database_url()
    engine = create_engine(url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-proof-escrow",
            amount=40,
            currency="MNT",
            witness_id="pg-proof-witness",
        ),
        engine=engine,
    )

    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative
    assert runtime._postgres_release is None

    for base in (AtomicLedgerBase, EscrowBase, OutboxBase, IdempotencyBase, TransactionWitness):
        base.metadata.drop_all(engine)

    # Recreate only through the production factory path.
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    session_factory = factory.session_factory
    now = datetime.now(timezone.utc)

    with session_factory() as session:
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "SRC", "MNT", 100)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "pg-proof-escrow", "MNT", 0)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "BEN", "MNT", 0)
        session.add(
            CanonicalEscrow(
                id="pg-proof-escrow",
                sender_address="SRC",
                receiver_address="BEN",
                amount=40,
                state="CREATED",
                condition_desc="production-proof",
                refund_destination="SRC",
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    with session_factory() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="pg-proof-fund",
            escrow_id="pg-proof-escrow",
            source="SRC",
            amount=40,
            currency="MNT",
        )
        session.commit()

    with session_factory() as session:
        lock_escrow_in_transaction(
            session,
            transaction_id="pg-proof-lock",
            escrow_id="pg-proof-escrow",
        )
        session.commit()

    with session_factory() as session:
        release_escrow_in_transaction(
            session,
            transaction_id="pg-proof-release",
            escrow_id="pg-proof-escrow",
            beneficiary="BEN",
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

    with session_factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

        from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel
        source = session.get(LedgerAccountModel, "SRC")
        escrow_account = session.get(LedgerAccountModel, "pg-proof-escrow")
        beneficiary = session.get(LedgerAccountModel, "BEN")
        movement_count = session.query(LedgerMovementModel).count()

        assert source.balance == 60
        assert escrow_account.balance == 0
        assert beneficiary.balance == 40
        assert movement_count == 2
        assert session.get(CanonicalEscrow, "pg-proof-escrow").state == "RELEASED"

    # A fresh factory against the same PostgreSQL state must still select the
    # Canonical Ledger and never restore the legacy release authority.
    restarted = ProductionRuntimeFactory(
        factory.config,
        engine=engine,
    ).create()
    assert restarted.is_canonical_ledger_authoritative
    assert restarted._postgres_release is None

    with session_factory() as session:
        for model in (
            TransactionWitness,
            CanonicalEscrow,
        ):
            session.execute(delete(model))
        session.commit()

    engine.dispose()

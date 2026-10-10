from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


pytestmark = pytest.mark.integration


def _database_url() -> str:
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url or not url.startswith("postgresql"):
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is not configured")
    return url


def test_production_postgresql_boot_fund_lock_and_deep_reconciliation():
    url = _database_url()
    escrow_id = "pg-integration-escrow"
    source = "pg-integration-source"

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id=escrow_id,
            amount=100,
            currency="MNT",
            witness_id="pg-integration-witness",
        )
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    with factory.session_factory() as session:
        now = datetime.now(timezone.utc)
        session.add(
            CanonicalEscrow(
                id=escrow_id,
                sender_address=source,
                receiver_address="beneficiary",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="integration",
                refund_destination=source,
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    runtime.create_account(source, initial_balance=100)
    runtime.create_account(escrow_id, initial_balance=0)

    funded = runtime.fund("pg-fund-1", source, "2026-10-06T00:00:00Z", {"test": "postgres"})
    assert not funded["replayed"]

    locked = runtime.lock("pg-lock-1", "2026-10-06T00:00:01Z", {"test": "postgres"})
    assert not locked["replayed"]

    with factory.session_factory() as session:
        source_account = session.get(LedgerAccountModel, source)
        escrow_account = session.get(LedgerAccountModel, escrow_id)
        escrow = session.get(CanonicalEscrow, escrow_id)
        movements = session.execute(select(LedgerMovementModel)).scalars().all()
        report = deep_reconcile_value_truth(session)

        assert source_account.balance == 0
        assert escrow_account.balance == 100
        assert escrow.state == EscrowState.LOCKED.value
        assert len(movements) == 1
        assert movements[0].transaction_id == "pg-fund-1"
        assert movements[0].operation == "FUND"
        assert report.matched, report.issues


def _runtime(factory, escrow_id, source, amount=100):
    runtime = factory.create()
    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        session.add(
            CanonicalEscrow(
                id=escrow_id,
                sender_address=source,
                receiver_address="beneficiary",
                amount=amount,
                state=EscrowState.CREATED.value,
                condition_desc="integration",
                refund_destination=source,
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()
    runtime.create_account(source, initial_balance=amount)
    runtime.create_account(escrow_id, initial_balance=0)
    return runtime


def test_production_postgresql_full_eai_value_graph():
    url = _database_url()
    zero_key = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    from dee_security.root_of_trust import RootOfTrust

    # RELEASE graph
    release_factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(url, "pg-release", 100, "MNT", "w-release")
    )
    release_runtime = _runtime(release_factory, "pg-release", "pg-source")
    release_runtime.create_account("beneficiary", initial_balance=0)
    release_runtime.fund("pg-fund-release", "pg-source", "2026-10-06T00:01:00Z", {"test": "postgres"})
    release_runtime.lock("pg-lock-release", "2026-10-06T00:01:01Z", {"test": "postgres"})
    release_runtime.release(
        transaction_id="pg-release-1",
        destination="beneficiary",
        timestamp="2026-10-06T00:01:02Z",
        evidence={"test": "postgres"},
        root=RootOfTrust("owner", zero_key),
        owner_id="owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )

    # REFUND graph: requested destination is intentionally not authoritative.
    refund_factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(url, "pg-refund", 100, "MNT", "w-refund")
    )
    refund_runtime = _runtime(refund_factory, "pg-refund", "pg-refund-source")
    refund_runtime.create_account("attacker", initial_balance=0)
    refund_runtime.fund("pg-fund-refund", "pg-refund-source", "2026-10-06T00:02:00Z", {"test": "postgres"})
    refund_runtime.lock("pg-lock-refund", "2026-10-06T00:02:01Z", {"test": "postgres"})
    refund_runtime.refund(
        transaction_id="pg-refund-1",
        destination="attacker",
        timestamp="2026-10-06T00:02:02Z",
        evidence={"test": "postgres"},
        root=RootOfTrust("owner", zero_key),
        owner_id="owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )

    # CANCEL graph: FUNDED cancellation reverses to the authoritative sender.
    cancel_factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(url, "pg-cancel", 100, "MNT", "w-cancel")
    )
    cancel_runtime = _runtime(cancel_factory, "pg-cancel", "pg-cancel-source")
    cancel_runtime.fund("pg-fund-cancel", "pg-cancel-source", "2026-10-06T00:03:00Z", {"test": "postgres"})
    cancel_runtime.cancel(
        transaction_id="pg-cancel-1",
        timestamp="2026-10-06T00:03:01Z",
        evidence={"test": "postgres"},
    )

    # SETTLEMENT uses the same Canonical Ledger authority.
    settle_factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(url, "pg-settlement", 1, "MNT", "w-settlement")
    )
    settle_runtime = settle_factory.create()
    settle_runtime.create_account("settle-source", initial_balance=50)
    settle_runtime.create_account("settle-destination", initial_balance=0)
    settle_runtime.settle(
        transaction_id="pg-settlement-1",
        source="settle-source",
        destination="settle-destination",
        amount=20,
        currency="MNT",
    )

    with release_factory.session_factory() as session:
        release_beneficiary = session.get(LedgerAccountModel, "beneficiary")
        refund_source = session.get(LedgerAccountModel, "pg-refund-source")
        attacker = session.get(LedgerAccountModel, "attacker")
        cancel_source = session.get(LedgerAccountModel, "pg-cancel-source")
        settlement_destination = session.get(LedgerAccountModel, "settle-destination")
        assert release_beneficiary.balance == 100
        assert refund_source.balance == 100
        assert attacker.balance == 0
        assert cancel_source.balance == 100
        assert settlement_destination.balance == 20

        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

from __future__ import annotations

import base64
import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from dee_security.root_of_trust import RootOfTrust
from persistence.atomic_ledger import LedgerAccountModel
from persistence.atomic_value_transaction import TransactionWitness
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)

pytestmark = pytest.mark.integration


def test_postgresql_production_runtime_boot_and_value_truth():
    url = os.environ["GERCHAIN_TEST_DATABASE_URL"]
    assert url.startswith("postgresql")

    engine = create_engine(url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-escrow-1",
            amount=40,
            currency="USD",
            witness_id="pg-w-1",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    runtime.create_account("pg-alice", 100)
    runtime.create_account("pg-escrow-1", 0)
    runtime.create_account("pg-bob", 0)
    runtime.create_escrow(
        escrow_id="pg-escrow-1",
        sender="pg-alice",
        beneficiary="pg-bob",
        refund_destination="pg-alice",
        amount=40,
        currency="USD",
        condition="production-postgresql-reperformance",
    )

    funded = runtime.fund(
        "pg-fund-1", "pg-alice", "T0", {"evidence": "ok"}
    )
    assert funded["replayed"] is False

    locked = runtime.lock("pg-lock-1", "T1", {"evidence": "ok"})
    assert locked["replayed"] is False

    released = runtime.release(
        transaction_id="pg-release-1",
        destination="pg-bob",
        timestamp="T2",
        evidence={"evidence": "ok"},
        root=RootOfTrust(
            "pg-owner",
            base64.b64encode(bytes(32)).decode("ascii"),
        ),
        owner_id="pg-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={
            "trust": True,
            "transparency": True,
            "performance": True,
        },
    )
    assert released["replayed"] is False

    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, [
            f"{i.code}:{i.transaction_id}:{i.detail}" for i in report.issues
        ]

        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "pg-escrow-1")
        ).scalar_one()
        assert escrow.state == EscrowState.RELEASED.value

        balances = {
            row.account_id: int(row.balance)
            for row in session.execute(select(LedgerAccountModel)).scalars()
            if row.account_id in {"pg-alice", "pg-escrow-1", "pg-bob"}
        }
        assert balances == {
            "pg-alice": 60,
            "pg-escrow-1": 0,
            "pg-bob": 40,
        }
        assert session.query(TransactionWitness).count() == 3

    engine.dispose()

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from persistence.atomic_ledger import LedgerAccountModel
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


DB_URL = os.environ.get("GERCHAIN_DATABASE_URL")


@pytest.mark.skipif(not DB_URL, reason="PostgreSQL re-performance requires GERCHAIN_DATABASE_URL")
def test_postgres_canonical_fund_lock_release_and_reconcile():
    cfg = ProductionRuntimeConfig(
        database_url=DB_URL,
        escrow_id="ea35-postgres-escrow",
        amount=100,
        currency="USD",
        witness_id="ea35-postgres-witness",
    )
    factory = ProductionRuntimeFactory(cfg)
    runtime = factory.create()
    sf = factory.session_factory
    now = datetime.now(timezone.utc)

    with sf.begin() as session:
        for account_id, balance in (("EA35-SRC", 100), ("EA35-BEN", 0), ("ea35-postgres-escrow", 0)):
            if session.get(LedgerAccountModel, account_id) is None:
                session.add(LedgerAccountModel(
                    account_id=account_id,
                    currency="USD",
                    balance=balance,
                    version=0,
                    updated_at=now,
                ))
        if session.get(CanonicalEscrow, "ea35-postgres-escrow") is None:
            session.add(CanonicalEscrow(
                id="ea35-postgres-escrow",
                sender_address="EA35-SRC",
                receiver_address="EA35-BEN",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="EA35 PostgreSQL re-performance",
                refund_destination="EA35-SRC",
                currency="USD",
                version=0,
                created_at=now,
                updated_at=now,
            ))

    assert runtime.fund("ea35-fund", "EA35-SRC", "T1", {"verified": True})["replayed"] is False
    assert runtime.lock("ea35-lock", "T2", {"verified": True})["replayed"] is False

    result = runtime.release(
        transaction_id="ea35-release",
        destination="EA35-BEN",
        timestamp="T3",
        evidence={"verified": True},
        root=object(),
        owner_id="ea35-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )
    assert result["replayed"] is False

    replay = runtime.release(
        transaction_id="ea35-release",
        destination="EA35-BEN",
        timestamp="T3",
        evidence={"verified": True},
        root=object(),
        owner_id="ea35-owner",
        authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )
    assert replay["replayed"] is True

    with sf() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}:{i.transaction_id}:{i.detail}" for i in report.issues]
        assert session.get(LedgerAccountModel, "EA35-SRC").balance == 0
        assert session.get(LedgerAccountModel, "EA35-BEN").balance == 100
        assert session.get(CanonicalEscrow, "ea35-postgres-escrow").state == EscrowState.RELEASED.value

    factory.engine.dispose()

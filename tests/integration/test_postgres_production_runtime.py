from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


@pytest.mark.integration
def test_production_runtime_postgresql_full_value_truth_path():
    url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_DATABASE_URL is required")
    engine = create_engine(url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="esc-prod-1",
            amount=40,
            currency="USD",
            witness_id="wit-prod-1",
        ),
        engine=engine,
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    sf = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    with sf() as session:
        session.add_all(
            [
                LedgerAccountModel(account_id="SRC", currency="USD", balance=100, version=0, updated_at=now),
                LedgerAccountModel(account_id="esc-prod-1", currency="USD", balance=0, version=0, updated_at=now),
                LedgerAccountModel(account_id="DST", currency="USD", balance=0, version=0, updated_at=now),
                CanonicalEscrow(
                    id="esc-prod-1",
                    sender_address="SRC",
                    receiver_address="DST",
                    amount=40,
                    state=EscrowState.CREATED.value,
                    condition_desc="production integration",
                    refund_destination="SRC",
                    currency="USD",
                    version=0,
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        session.commit()

    assert runtime.fund("fund-prod-1", "SRC", "T1", {"case": "postgres"})["replayed"] is False
    assert runtime.lock("lock-prod-1", "T2", {"case": "postgres"})["replayed"] is False

    from persistence.release_escrow import release_escrow_in_transaction

    with sf() as session:
        result = release_escrow_in_transaction(
            session,
            transaction_id="release-prod-1",
            escrow_id="esc-prod-1",
            beneficiary="DST",
            amount=40,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
            payload={"case": "postgres"},
        )
        session.commit()
        assert result["replayed"] is False

    assert runtime.get_balance("SRC") == 60
    assert runtime.get_balance("esc-prod-1") == 0
    assert runtime.get_balance("DST") == 40
    assert runtime.get_escrow_state()["state"] == EscrowState.RELEASED.value

    with sf() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    engine.dispose()

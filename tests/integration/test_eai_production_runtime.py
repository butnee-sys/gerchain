from __future__ import annotations

import os
from datetime import datetime, timezone

from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_postgresql_runtime_boot_and_canonical_value_flow():
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=os.environ["GERCHAIN_DATABASE_URL"],
            escrow_id="ci-escrow",
            amount=100,
            currency="USD",
            witness_id="ci-witness",
        )
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    now = datetime.now(timezone.utc)
    with factory.session_factory() as session:
        from persistence.atomic_ledger import PostgreSQLAtomicLedger
        ledger = PostgreSQLAtomicLedger(factory.session_factory)
        ledger.create_account_in_transaction(session, "SRC", "USD", 100)
        ledger.create_account_in_transaction(session, "ci-escrow", "USD", 0)
        ledger.create_account_in_transaction(session, "DST", "USD", 0)
        session.add(CanonicalEscrow(
            id="ci-escrow", sender_address="SRC", receiver_address="DST",
            refund_destination="SRC", amount=100, state="CREATED",
            condition_desc="CI production gate", currency="USD", version=0,
            created_at=now, updated_at=now,
        ))
        session.commit()

    runtime.fund("ci-fund", "SRC", now.isoformat(), {"source": "ci"})
    runtime.lock("ci-lock", now.isoformat(), {"source": "ci"})
    runtime.release(
        transaction_id="ci-release", destination="DST",
        timestamp=now.isoformat(), evidence={"source": "ci"},
        root=object(), owner_id="ci-owner", authorized=True,
        evidence_verified=True,
        trinity_proof={"trust": True, "transparency": True, "performance": True},
    )

    assert runtime.get_balance("SRC") == 0
    assert runtime.get_balance("ci-escrow") == 0
    assert runtime.get_balance("DST") == 100
    assert runtime.get_escrow_state()["state"] == "RELEASED"

    with factory.session_factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, report.issues

    factory.engine.dispose()

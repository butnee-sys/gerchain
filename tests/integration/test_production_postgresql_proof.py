from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.escrow_aggregate import CanonicalEscrow
from persistence.recovery_outbox import OutboxEvent
from persistence.atomic_value_transaction import TransactionWitness
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


@pytest.mark.integration
def test_production_postgresql_boot_and_canonical_value_flow():
    url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not url:
        raise RuntimeError("GERCHAIN_DATABASE_URL is required for PostgreSQL production proof")
    engine = create_engine(url, future=True, pool_pre_ping=True)
    sf = sessionmaker(bind=engine, expire_on_commit=False)
    runtime = ProductionRuntimeFactory.create(
        escrow_id="pg-proof-escrow", amount=100, currency="USD", witness_id="pg-proof-witness",
        engine=engine, session_factory=sf,
    )
    assert runtime.is_canonical_ledger_authoritative
    assert runtime._canonical_ledger is not None

    sf = sessionmaker(bind=engine, expire_on_commit=False)
    with sf() as session:
        runtime._canonical_ledger.create_account_in_transaction(session, "PG-SOURCE", "USD", 1000)
        runtime._canonical_ledger.create_account_in_transaction(session, "pg-proof-escrow", "USD", 0)
        runtime._canonical_ledger.create_account_in_transaction(session, "PG-BENEFICIARY", "USD", 0)
        session.add(CanonicalEscrow(
            id="pg-proof-escrow",
            sender_address="PG-SOURCE",
            receiver_address="PG-BENEFICIARY",
            refund_destination="PG-SOURCE",
            amount=100,
            state="CREATED",
            condition_desc="integration-proof",
            currency="USD",
            version=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ))
        session.commit()

    with sf() as session:
        fund_escrow_in_transaction(
            session, transaction_id="pg-fund-1", escrow_id="pg-proof-escrow",
            source="PG-SOURCE", amount=100, currency="USD", payload={"proof": "fund"},
        )
        session.commit()

    with sf() as session:
        lock_escrow_in_transaction(
            session, transaction_id="pg-lock-1", escrow_id="pg-proof-escrow",
            payload={"proof": "lock"},
        )
        session.commit()

    with sf() as session:
        release_escrow_in_transaction(
            session, transaction_id="pg-release-1", escrow_id="pg-proof-escrow",
            beneficiary="PG-BENEFICIARY", amount=100, currency="USD",
            decision_status="APPROVE", authorization_status="AUTHORIZED",
            trust=True, transparency=True, performance=True,
            evidence_verified=True, payload={"proof": "release"},
        )
        session.commit()

    with sf() as session:
        balances = {
            row.account_id: row.balance
            for row in session.execute(select(LedgerAccountModel)).scalars()
        }
        assert balances == {
            "PG-SOURCE": 900,
            "pg-proof-escrow": 0,
            "PG-BENEFICIARY": 100,
        }
        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "pg-proof-escrow")
        ).scalar_one()
        assert escrow.state == "RELEASED"
        report = deep_reconcile_value_truth(session)
        assert report.matched, [f"{i.code}:{i.transaction_id}:{i.detail}" for i in report.issues]
        assert session.execute(select(TransactionWitness)).scalars().all()
        assert session.execute(select(OutboxEvent)).scalars().all()

    engine.dispose()

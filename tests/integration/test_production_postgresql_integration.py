from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, PostgreSQLAtomicLedger
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


POSTGRES_URL = os.getenv("GERCHAIN_TEST_POSTGRES_URL")


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="set GERCHAIN_TEST_POSTGRES_URL to run the real PostgreSQL production re-performance",
)
def test_production_postgresql_boot_and_canonical_value_flow():
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    escrow_id = "eai-prod-test-escrow"
    source = "eai-prod-test-source"
    beneficiary = "eai-prod-test-beneficiary"

    try:
        factory = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=POSTGRES_URL,
                escrow_id=escrow_id,
                amount=100,
                currency="MNT",
                witness_id="eai-prod-test-witness",
            ),
            engine=engine,
        )
        runtime = factory.create()

        assert runtime.is_canonical_ledger_authoritative
        assert engine.dialect.name == "postgresql"

        tables = set(inspect(engine).get_table_names())
        assert {
            "escrows",
            "gerchain_ledger_accounts",
            "gerchain_ledger_movements",
            "gerchain_transaction_witnesses",
            "gerchain_outbox_events",
            "gerchain_idempotency_records",
            "schema_version",
        }.issubset(tables)

        Session = sessionmaker(bind=engine, expire_on_commit=False)
        now = datetime.now(timezone.utc)

        with Session() as session:
            for account_id, balance in ((source, 100), (escrow_id, 0), (beneficiary, 0)):
                PostgreSQLAtomicLedger.create_account_in_transaction(
                    session, account_id, "MNT", balance
                )
            session.add(
                CanonicalEscrow(
                    id=escrow_id,
                    sender_address=source,
                    receiver_address=beneficiary,
                    amount=Decimal("100"),
                    state=EscrowState.CREATED.value,
                    condition_desc="production integration",
                    refund_destination=source,
                    currency="MNT",
                    version=0,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.commit()

        with Session() as session:
            fund_escrow_in_transaction(
                session,
                transaction_id="eai-prod-fund-1",
                escrow_id=escrow_id,
                source=source,
                amount=100,
                currency="MNT",
            )
            session.commit()

        with Session() as session:
            lock_escrow_in_transaction(
                session,
                transaction_id="eai-prod-lock-1",
                escrow_id=escrow_id,
            )
            session.commit()

        with Session() as session:
            release_escrow_in_transaction(
                session,
                transaction_id="eai-prod-release-1",
                escrow_id=escrow_id,
                beneficiary=beneficiary,
                amount=100,
                currency="MNT",
                decision_status="APPROVE",
                authorization_status="AUTHORIZED",
                trust=True,
                transparency=True,
                performance=True,
                evidence_verified=True,
            )
            session.commit()

        with Session() as session:
            escrow = session.execute(
                select(CanonicalEscrow).where(CanonicalEscrow.id == escrow_id)
            ).scalar_one()
            accounts = {
                row.account_id: row.balance
                for row in session.execute(select(LedgerAccountModel)).scalars()
                if row.account_id in {source, escrow_id, beneficiary}
            }
            report = deep_reconcile_value_truth(session)

        assert escrow.state == EscrowState.RELEASED.value
        assert accounts == {source: 0, escrow_id: 0, beneficiary: 100}
        assert report.matched is True
    finally:
        engine.dispose()

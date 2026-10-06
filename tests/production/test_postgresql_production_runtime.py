from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, PostgreSQLAtomicLedger
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_factory_boots_and_completes_canonical_value_flow() -> None:
    database_url = os.environ["GERCHAIN_POSTGRES_DSN"]
    engine = create_engine(database_url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="esc-prod-1",
            amount=50,
            currency="USD",
            witness_id="wit-prod-1",
        ),
        engine=engine,
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    with sessions() as session:
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, "SRC-PROD", "USD", 100
        )
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, "esc-prod-1", "USD", 0
        )
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, "DST-PROD", "USD", 0
        )
        session.add(
            CanonicalEscrow(
                id="esc-prod-1",
                sender_address="SRC-PROD",
                receiver_address="DST-PROD",
                amount=50,
                state=EscrowState.CREATED.value,
                condition_desc="production integration",
                refund_destination="SRC-PROD",
                currency="USD",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    with sessions() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="prod-fund-1",
            escrow_id="esc-prod-1",
            source="SRC-PROD",
            amount=50,
            currency="USD",
        )
        session.commit()

    with sessions() as session:
        lock_escrow_in_transaction(
            session,
            transaction_id="prod-lock-1",
            escrow_id="esc-prod-1",
        )
        session.commit()

    with sessions() as session:
        release_escrow_in_transaction(
            session,
            transaction_id="prod-release-1",
            escrow_id="esc-prod-1",
            beneficiary="DST-PROD",
            amount=50,
            currency="USD",
            decision_status="APPROVE",
            authorization_status="AUTHORIZED",
            trust=True,
            transparency=True,
            performance=True,
            evidence_verified=True,
        )
        session.commit()

    with sessions() as session:
        balances = {
            row.account_id: int(row.balance)
            for row in session.execute(
                select(LedgerAccountModel).where(
                    LedgerAccountModel.account_id.in_(
                        ["SRC-PROD", "esc-prod-1", "DST-PROD"]
                    )
                )
            ).scalars()
        }
        escrow = session.get(CanonicalEscrow, "esc-prod-1")
        report = deep_reconcile_value_truth(session)

        assert balances == {
            "SRC-PROD": 50,
            "esc-prod-1": 0,
            "DST-PROD": 50,
        }
        assert escrow is not None
        assert escrow.state == EscrowState.RELEASED.value
        assert report.matched
        assert report.canonical_movement_count == 2

    engine.dispose()

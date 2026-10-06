from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from services.gerchain_runtime_factory import ProductionRuntimeFactory


def test_production_postgresql_canonical_value_flow():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    try:
        factory = ProductionRuntimeFactory.from_engine(
            escrow_id="eai-pg-smoke",
            amount=100,
            currency="MNT",
            witness_id="witness-pg-smoke",
            engine=engine,
        )
        runtime = factory
        assert runtime.is_canonical_ledger_authoritative

        Session = sessionmaker(bind=engine, expire_on_commit=False)
        now = datetime.now(timezone.utc)

        with Session() as session:
            session.add_all([
                LedgerAccountModel(
                    account_id="pg-source",
                    currency="MNT",
                    balance=100,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="eai-pg-smoke",
                    currency="MNT",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="pg-beneficiary",
                    currency="MNT",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
                CanonicalEscrow(
                    id="eai-pg-smoke",
                    sender_address="pg-source",
                    receiver_address="pg-beneficiary",
                    amount=100,
                    state="CREATED",
                    condition_desc="production-postgresql-smoke",
                    refund_destination="pg-source",
                    currency="MNT",
                    version=0,
                    created_at=now,
                    updated_at=now,
                ),
            ])
            session.commit()

        with Session() as session:
            result = fund_escrow_in_transaction(
                session,
                transaction_id="pg-fund-1",
                escrow_id="eai-pg-smoke",
                source="pg-source",
                amount=100,
                currency="MNT",
            )
            session.commit()
            assert result["replayed"] is False

        with Session() as session:
            result = lock_escrow_in_transaction(
                session,
                transaction_id="pg-lock-1",
                escrow_id="eai-pg-smoke",
            )
            session.commit()
            assert result["status"] == "LOCKED"

        with Session() as session:
            result = release_escrow_in_transaction(
                session,
                transaction_id="pg-release-1",
                escrow_id="eai-pg-smoke",
                beneficiary="pg-beneficiary",
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
            assert result["replayed"] is False

        with Session() as session:
            source = session.execute(
                select(LedgerAccountModel).where(
                    LedgerAccountModel.account_id == "pg-source"
                )
            ).scalar_one()
            escrow_account = session.execute(
                select(LedgerAccountModel).where(
                    LedgerAccountModel.account_id == "eai-pg-smoke"
                )
            ).scalar_one()
            beneficiary = session.execute(
                select(LedgerAccountModel).where(
                    LedgerAccountModel.account_id == "pg-beneficiary"
                )
            ).scalar_one()
            escrow = session.execute(
                select(CanonicalEscrow).where(
                    CanonicalEscrow.id == "eai-pg-smoke"
                )
            ).scalar_one()

            assert source.balance == 0
            assert escrow_account.balance == 0
            assert beneficiary.balance == 100
            assert escrow.state == "RELEASED"
            assert escrow.version == 3

            report = deep_reconcile_value_truth(session)
            assert report.matched, report.issues
    finally:
        engine.dispose()

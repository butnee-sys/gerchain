from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_postgres_fund_lock_release_deep_reconcile():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-smoke-escrow",
            amount=100,
            currency="MNT",
            witness_id="pg-smoke-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    with sessions() as session:
        session.query(LedgerAccountModel).filter(
            LedgerAccountModel.account_id.in_(
                ["pg-smoke-source", "pg-smoke-escrow", "pg-smoke-beneficiary"]
            )
        ).delete(synchronize_session=False)
        session.query(CanonicalEscrow).filter(
            CanonicalEscrow.id == "pg-smoke-escrow"
        ).delete(synchronize_session=False)
        session.commit()

        session.add_all(
            [
                LedgerAccountModel(
                    account_id="pg-smoke-source",
                    currency="MNT",
                    balance=100,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="pg-smoke-escrow",
                    currency="MNT",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
                LedgerAccountModel(
                    account_id="pg-smoke-beneficiary",
                    currency="MNT",
                    balance=0,
                    version=0,
                    updated_at=now,
                ),
            ]
        )
        session.add(
            CanonicalEscrow(
                id="pg-smoke-escrow",
                sender_address="pg-smoke-source",
                receiver_address="pg-smoke-beneficiary",
                amount=100,
                state=EscrowState.CREATED.value,
                condition_desc="production smoke",
                refund_destination="pg-smoke-source",
                currency="MNT",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    with sessions() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="pg-smoke-fund",
            escrow_id="pg-smoke-escrow",
            source="pg-smoke-source",
            amount=100,
            currency="MNT",
        )
        session.commit()

    with sessions() as session:
        lock_escrow_in_transaction(
            session,
            transaction_id="pg-smoke-lock",
            escrow_id="pg-smoke-escrow",
        )
        session.commit()

    with sessions() as session:
        release_escrow_in_transaction(
            session,
            transaction_id="pg-smoke-release",
            escrow_id="pg-smoke-escrow",
            beneficiary="pg-smoke-beneficiary",
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

    with sessions() as session:
        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "pg-smoke-escrow")
        ).scalar_one()
        source = session.get(LedgerAccountModel, "pg-smoke-source")
        escrow_account = session.get(LedgerAccountModel, "pg-smoke-escrow")
        beneficiary = session.get(LedgerAccountModel, "pg-smoke-beneficiary")
        report = deep_reconcile_value_truth(session)

        assert escrow.state == EscrowState.RELEASED.value
        assert source.balance == 0
        assert escrow_account.balance == 0
        assert beneficiary.balance == 100
        assert report.matched

    engine.dispose()

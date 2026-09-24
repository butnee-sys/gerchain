from __future__ import annotations

import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.create_escrow import create_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.escrow_aggregate import CanonicalEscrow


def test_real_postgresql_canonical_value_path() -> None:
    url = os.environ["GERCHAIN_TEST_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    with factory() as session:
        create_escrow_in_transaction(
            session,
            escrow_id="pg-it-escrow",
            source="pg-it-source",
            beneficiary="pg-it-beneficiary",
            refund_destination="pg-it-source",
            amount=100,
            currency="MNT",
            condition="integration-test",
        )
        session.add_all([
            LedgerAccountModel(
                account_id="pg-it-source",
                currency="MNT",
                balance=100,
                version=0,
            ),
            LedgerAccountModel(
                account_id="pg-it-escrow",
                currency="MNT",
                balance=0,
                version=0,
            ),
            LedgerAccountModel(
                account_id="pg-it-beneficiary",
                currency="MNT",
                balance=0,
                version=0,
            ),
        ])
        session.commit()

        fund_escrow_in_transaction(
            session,
            transaction_id="pg-it-fund",
            escrow_id="pg-it-escrow",
            source="pg-it-source",
            amount=100,
            currency="MNT",
        )
        session.commit()

        lock_escrow_in_transaction(
            session,
            transaction_id="pg-it-lock",
            escrow_id="pg-it-escrow",
        )
        session.commit()

        release_escrow_in_transaction(
            session,
            transaction_id="pg-it-release",
            escrow_id="pg-it-escrow",
            beneficiary="pg-it-beneficiary",
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

        escrow = session.execute(
            select(CanonicalEscrow).where(CanonicalEscrow.id == "pg-it-escrow")
        ).scalar_one()
        balances = {
            row.account_id: row.balance
            for row in session.execute(
                select(LedgerAccountModel).where(
                    LedgerAccountModel.account_id.in_(
                        ["pg-it-source", "pg-it-escrow", "pg-it-beneficiary"]
                    )
                )
            ).scalars()
        }
        report = deep_reconcile_value_truth(session)

        assert escrow.state == "RELEASED"
        assert balances == {
            "pg-it-source": 0,
            "pg-it-escrow": 0,
            "pg-it-beneficiary": 100,
        }
        assert report.matched

    engine.dispose()

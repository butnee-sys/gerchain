from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def _factory(url: str, escrow_id: str) -> tuple[object, sessionmaker]:
    engine = create_engine(url, pool_pre_ping=True)
    ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id=escrow_id,
            amount=50,
            currency="USD",
            witness_id=f"{escrow_id}-witness",
        ),
        engine=engine,
    ).create()
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def _seed(sf, escrow_id: str, source: str, beneficiary: str, amount: int = 50) -> None:
    now = datetime.now(timezone.utc)
    with sf() as session:
        for account_id, balance in ((source, amount), (beneficiary, 0), (escrow_id, 0)):
            session.add(
                LedgerAccountModel(
                    account_id=account_id,
                    currency="USD",
                    balance=balance,
                    version=0,
                    updated_at=now,
                )
            )
        session.add(
            CanonicalEscrow(
                id=escrow_id,
                sender_address=source,
                receiver_address=beneficiary,
                refund_destination=source,
                amount=amount,
                state=EscrowState.CREATED.value,
                condition_desc="EA-35 PostgreSQL lifecycle proof",
                currency="USD",
                version=0,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()


def test_postgres_refund_and_cancel_are_canonical_and_reconciled() -> None:
    url = os.environ["GERCHAIN_DATABASE_URL"]

    refund_engine, refund_sf = _factory(url, "pg-refund-proof")
    _seed(refund_sf, "pg-refund-proof", "refund-source", "refund-beneficiary")

    from persistence.fund_escrow import fund_escrow_in_transaction
    from persistence.lock_escrow import lock_escrow_in_transaction
    from persistence.refund_escrow import refund_escrow_in_transaction

    with refund_sf() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="pg-refund-fund",
            escrow_id="pg-refund-proof",
            source="refund-source",
            amount=50,
            currency="USD",
        )
        session.commit()
    with refund_sf() as session:
        lock_escrow_in_transaction(
            session,
            transaction_id="pg-refund-lock",
            escrow_id="pg-refund-proof",
        )
        session.commit()
    with refund_sf() as session:
        refund_escrow_in_transaction(
            session,
            transaction_id="pg-refund",
            escrow_id="pg-refund-proof",
            amount=50,
            currency="USD",
            payload={"proof": "refund"},
        )
        session.commit()

    with refund_sf() as session:
        escrow = session.get(CanonicalEscrow, "pg-refund-proof")
        balances = {
            row.account_id: row.balance
            for row in session.execute(select(LedgerAccountModel)).scalars()
            if row.account_id in {"refund-source", "refund-beneficiary", "pg-refund-proof"}
        }
        report = deep_reconcile_value_truth(session)
        assert escrow.state == EscrowState.REFUNDED.value
        assert balances["refund-source"] == 50
        assert balances["refund-beneficiary"] == 0
        assert balances["pg-refund-proof"] == 0
        assert report.matched, [f"{i.code}:{i.transaction_id}:{i.detail}" for i in report.issues]

    refund_engine.dispose()

    cancel_engine, cancel_sf = _factory(url, "pg-cancel-proof")
    _seed(cancel_sf, "pg-cancel-proof", "cancel-source", "cancel-beneficiary")

    from persistence.cancel_escrow import cancel_escrow_in_transaction

    with cancel_sf() as session:
        fund_escrow_in_transaction(
            session,
            transaction_id="pg-cancel-fund",
            escrow_id="pg-cancel-proof",
            source="cancel-source",
            amount=50,
            currency="USD",
        )
        session.commit()
    with cancel_sf() as session:
        cancel_escrow_in_transaction(
            session,
            transaction_id="pg-cancel",
            escrow_id="pg-cancel-proof",
            payload={"proof": "cancel"},
        )
        session.commit()

    with cancel_sf() as session:
        escrow = session.get(CanonicalEscrow, "pg-cancel-proof")
        balances = {
            row.account_id: row.balance
            for row in session.execute(select(LedgerAccountModel)).scalars()
            if row.account_id in {"cancel-source", "cancel-beneficiary", "pg-cancel-proof"}
        }
        report = deep_reconcile_value_truth(session)
        assert escrow.state == EscrowState.CANCELLED.value
        assert balances["cancel-source"] == 50
        assert balances["cancel-beneficiary"] == 0
        assert balances["pg-cancel-proof"] == 0
        assert report.matched, [f"{i.code}:{i.transaction_id}:{i.detail}" for i in report.issues]

    cancel_engine.dispose()

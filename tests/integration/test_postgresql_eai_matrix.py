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
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.cancel_escrow import cancel_escrow_in_transaction
from persistence.atomic_ledger import LedgerMovementModel
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_postgresql_eai_refund_cancel_and_settlement_paths():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        config = ProductionRuntimeConfig(
            database_url=url,
            escrow_id="eai-matrix-refund",
            amount=100,
            currency="USD",
            witness_id="eai-matrix-witness",
        )
        runtime = ProductionRuntimeFactory(config, engine=engine).create()
        assert runtime.is_canonical_ledger_authoritative
        now = datetime.now(timezone.utc)

        with Session() as session:
            for account_id, balance in (
                ("MATRIX-SOURCE", 300),
                ("eai-matrix-refund", 0),
                ("MATRIX-REFUND", 0),
                ("MATRIX-BENEFICIARY", 0),
                ("eai-matrix-cancel", 0),
                ("MATRIX-CANCEL-SOURCE", 100),
                ("MATRIX-SETTLE-DEST", 0),
            ):
                session.add(
                    LedgerAccountModel(
                        account_id=account_id,
                        currency="USD",
                        balance=balance,
                        version=0,
                        updated_at=now,
                    )
                )
            session.add_all(
                [
                    CanonicalEscrow(
                        id="eai-matrix-refund",
                        sender_address="MATRIX-SOURCE",
                        receiver_address="MATRIX-BENEFICIARY",
                        refund_destination="MATRIX-REFUND",
                        amount=100,
                        state=EscrowState.CREATED.value,
                        condition_desc="refund-matrix",
                        currency="USD",
                        version=0,
                        created_at=now,
                        updated_at=now,
                    ),
                    CanonicalEscrow(
                        id="eai-matrix-cancel",
                        sender_address="MATRIX-CANCEL-SOURCE",
                        receiver_address="MATRIX-BENEFICIARY",
                        refund_destination="MATRIX-CANCEL-SOURCE",
                        amount=100,
                        state=EscrowState.CREATED.value,
                        condition_desc="cancel-matrix",
                        currency="USD",
                        version=0,
                        created_at=now,
                        updated_at=now,
                    ),
                ]
            )
            session.commit()

        with Session() as session:
            fund_escrow_in_transaction(
                session,
                transaction_id="matrix-refund-fund",
                escrow_id="eai-matrix-refund",
                source="MATRIX-SOURCE",
                amount=100,
                currency="USD",
            )
            session.commit()

        with Session() as session:
            lock_escrow_in_transaction(
                session,
                transaction_id="matrix-refund-lock",
                escrow_id="eai-matrix-refund",
            )
            session.commit()

        with Session() as session:
            refund_escrow_in_transaction(
                session,
                transaction_id="matrix-refund-refund",
                escrow_id="eai-matrix-refund",
                amount=100,
                currency="USD",
                payload={"matrix": "refund"},
            )
            session.commit()

        with Session() as session:
            fund_escrow_in_transaction(
                session,
                transaction_id="matrix-cancel-fund",
                escrow_id="eai-matrix-cancel",
                source="MATRIX-CANCEL-SOURCE",
                amount=100,
                currency="USD",
            )
            session.commit()

        with Session() as session:
            cancel_escrow_in_transaction(
                session,
                transaction_id="matrix-cancel-cancel",
                escrow_id="eai-matrix-cancel",
                payload={"matrix": "cancel"},
            )
            session.commit()

        runtime.settle(
            transaction_id="matrix-settlement",
            source="MATRIX-SOURCE",
            destination="MATRIX-SETTLE-DEST",
            amount=25,
            currency="USD",
        )

        with Session() as session:
            refund = session.get(CanonicalEscrow, "eai-matrix-refund")
            cancel = session.get(CanonicalEscrow, "eai-matrix-cancel")
            source = session.get(LedgerAccountModel, "MATRIX-SOURCE")
            refund_account = session.get(LedgerAccountModel, "MATRIX-REFUND")
            cancel_source = session.get(LedgerAccountModel, "MATRIX-CANCEL-SOURCE")
            settlement_dest = session.get(LedgerAccountModel, "MATRIX-SETTLE-DEST")

            assert refund.state == EscrowState.REFUNDED.value
            assert cancel.state == EscrowState.CANCELLED.value
            assert source.balance == 175
            assert refund_account.balance == 100
            assert cancel_source.balance == 100
            assert settlement_dest.balance == 25

            report = deep_reconcile_value_truth(session)
            assert report.matched, [
                f"{i.code}:{i.transaction_id}:{i.detail}" for i in report.issues
            ]
    finally:
        engine.dispose()

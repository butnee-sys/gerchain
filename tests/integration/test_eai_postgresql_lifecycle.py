from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel, PostgreSQLAtomicLedger
from persistence.cancel_escrow import cancel_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.settlement_coordinator import SettlementCoordinator
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def _seed_escrow(session, escrow_id: str, *, sender: str, refund_destination: str | None) -> None:
    now = datetime.now(timezone.utc)
    session.add(
        CanonicalEscrow(
            id=escrow_id,
            sender_address=sender,
            receiver_address="BENEFICIARY",
            amount=100,
            state=EscrowState.CREATED.value,
            condition_desc="integration",
            refund_destination=refund_destination,
            currency="MNT",
            version=0,
            created_at=now,
            updated_at=now,
        )
    )


def test_eai_postgresql_canonical_value_lifecycle_and_reconciliation():
    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, future=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    try:
        runtime = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=url,
                escrow_id="eai-release",
                amount=100,
                currency="MNT",
                witness_id="eai-witness",
            ),
            engine=engine,
        ).create()
        assert runtime.is_canonical_ledger_authoritative

        with factory() as session:
            for account in ("SRC", "BENEFICIARY", "REFUND", "CANCEL-SRC", "SETTLE"):
                PostgreSQLAtomicLedger.create_account_in_transaction(
                    session, account, "MNT", 1000 if account in ("SRC", "CANCEL-SRC", "SETTLE") else 0
                )
            _seed_escrow(session, "eai-release", sender="SRC", refund_destination="REFUND")
            _seed_escrow(session, "eai-refund", sender="SRC", refund_destination="REFUND")
            _seed_escrow(session, "eai-cancel", sender="CANCEL-SRC", refund_destination="CANCEL-SRC")
            session.commit()

        # RELEASE path: FUND -> LOCK -> RELEASE, all canonical and durable.
        with factory() as session:
            fund_escrow_in_transaction(
                session, transaction_id="eai-fund-release", escrow_id="eai-release",
                source="SRC", amount=100, currency="MNT", payload={"test": "fund"},
            )
            session.commit()
        with factory() as session:
            lock_escrow_in_transaction(
                session, transaction_id="eai-lock-release", escrow_id="eai-release",
                payload={"test": "lock"},
            )
            session.commit()
        with factory() as session:
            release_escrow_in_transaction(
                session, transaction_id="eai-release-tx", escrow_id="eai-release",
                beneficiary="BENEFICIARY", amount=100, currency="MNT",
                decision_status="APPROVE", authorization_status="AUTHORIZED",
                trust=True, transparency=True, performance=True,
                evidence_verified=True, payload={"test": "release"},
            )
            session.commit()

        # REFUND path: FUND -> LOCK -> REFUND; authoritative refund destination is escrow data.
        with factory() as session:
            fund_escrow_in_transaction(
                session, transaction_id="eai-fund-refund", escrow_id="eai-refund",
                source="SRC", amount=100, currency="MNT", payload={"test": "fund"},
            )
            lock_escrow_in_transaction(
                session, transaction_id="eai-lock-refund", escrow_id="eai-refund",
                payload={"test": "lock"},
            )
            session.commit()
        with factory() as session:
            refund_escrow_in_transaction(
                session, transaction_id="eai-refund-tx", escrow_id="eai-refund",
                amount=100, currency="MNT",
                payload={"test": "refund", "requested_destination": "ATTACKER"},
            )
            session.commit()

        # CANCEL path: FUNDED -> CANCELLED reverses value to the original sender.
        with factory() as session:
            fund_escrow_in_transaction(
                session, transaction_id="eai-fund-cancel", escrow_id="eai-cancel",
                source="CANCEL-SRC", amount=100, currency="MNT", payload={"test": "fund"},
            )
            session.commit()
        with factory() as session:
            cancel_escrow_in_transaction(
                session, transaction_id="eai-cancel-tx", escrow_id="eai-cancel",
                payload={"test": "cancel"},
            )
            session.commit()

        with factory() as session:
            report = deep_reconcile_value_truth(session)
            assert report.matched, [f"{i.code}: {i.detail}" for i in report.issues]

            movements = session.execute(select(LedgerMovementModel)).scalars().all()
            assert len(movements) == 6

            release = session.get(LedgerAccountModel, "BENEFICIARY")
            refund = session.get(LedgerAccountModel, "REFUND")
            cancel_src = session.get(LedgerAccountModel, "CANCEL-SRC")
            assert release.balance == 100
            assert refund.balance == 100
            assert cancel_src.balance == 1000

        # SETTLEMENT is a canonical Ledger operation but an orchestration path,
        # so it is checked independently from the value-truth evidence graph.
        with factory() as session:
            result = SettlementCoordinator(session).settle_in_transaction(
                transaction_id="eai-settlement-tx",
                source="SETTLE",
                destination="BENEFICIARY",
                amount=50,
                currency="MNT",
            )
            assert result["replayed"] is False
            session.commit()

        with factory() as session:
            settlement = session.execute(
                select(LedgerMovementModel).where(
                    LedgerMovementModel.transaction_id == "eai-settlement-tx"
                )
            ).scalar_one()
            assert settlement.operation == "SETTLEMENT"
            assert settlement.source == "SETTLE"
            assert settlement.destination == "BENEFICIARY"
            assert session.get(LedgerAccountModel, "SETTLE").balance == 950
            assert session.get(LedgerAccountModel, "BENEFICIARY").balance == 150
    finally:
        engine.dispose()

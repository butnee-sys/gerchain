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


def test_postgresql_failure_matrix_and_duplicate_fund_concurrency():
    """Real PostgreSQL failure/replay/concurrency matrix for the canonical path."""
    from concurrent.futures import ThreadPoolExecutor
    from persistence.fund_escrow import fund_escrow_in_transaction
    from persistence.atomic_value_transaction import TransactionWitness
    from persistence.recovery_outbox import OutboxEvent
    from persistence.durable_idempotency import DurableIdempotencyRecord
    from sqlalchemy import text

    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        runtime = ProductionRuntimeFactory(
            ProductionRuntimeConfig(url, "eai-failure-matrix", 40, "USD", "w-failure-matrix"),
            engine=engine,
        ).create()
        with Session.begin() as session:
            session.execute(text("DELETE FROM gerchain_ledger_movements"))
            session.execute(text("DELETE FROM gerchain_transaction_witnesses"))
            session.execute(text("DELETE FROM gerchain_outbox_events"))
            session.execute(text("DELETE FROM gerchain_idempotency_records"))
            session.execute(text("DELETE FROM gerchain_ledger_accounts"))
            session.execute(text("DELETE FROM escrows"))

        runtime.create_escrow(
            escrow_id="eai-failure-matrix", sender="FM-SOURCE", beneficiary="FM-BEN",
            refund_destination="FM-SOURCE", amount=40, currency="USD", condition="failure-matrix"
        )
        runtime.create_account("FM-SOURCE", initial_balance=50)
        runtime.create_account("eai-failure-matrix", initial_balance=0)

        # Invalid state transition: LOCK before FUND must fail without evidence or value movement.
        try:
            runtime.lock("fm-invalid-lock", datetime.now(timezone.utc).isoformat(), {"matrix": "invalid-lock"})
            raise AssertionError("LOCK before FUND unexpectedly succeeded")
        except ValueError:
            pass

        # Insufficient source balance must fail closed and leave the aggregate untouched.
        with Session() as session:
            try:
                fund_escrow_in_transaction(
                    session, transaction_id="fm-insufficient", escrow_id="eai-failure-matrix",
                    source="FM-SOURCE", amount=40, currency="USD",
                )
                raise AssertionError("insufficient FUND unexpectedly succeeded")
            except ValueError as exc:
                assert "Insufficient balance" in str(exc)
                session.rollback()

        # First valid FUND, then idempotency conflict with a changed request.
        runtime.fund("fm-fund", "FM-SOURCE", datetime.now(timezone.utc).isoformat(), {"matrix": "valid"})
        with Session() as session:
            try:
                fund_escrow_in_transaction(
                    session, transaction_id="fm-fund", escrow_id="eai-failure-matrix",
                    source="FM-SOURCE", amount=39, currency="USD",
                )
                raise AssertionError("idempotency conflict unexpectedly succeeded")
            except Exception as exc:
                assert "idempotency key reused with different request" in str(exc)
                session.rollback()

        with Session() as session:
            movement_count = session.query(LedgerMovementModel).count()
            witness_count = session.query(TransactionWitness).count()
            outbox_count = session.query(OutboxEvent).count()
            idem_count = session.query(DurableIdempotencyRecord).count()
            escrow = session.get(CanonicalEscrow, "eai-failure-matrix")
            source = session.get(LedgerAccountModel, "FM-SOURCE")
            assert movement_count == 1
            assert witness_count == 1
            assert outbox_count == 1
            assert idem_count == 1
            assert escrow.state == EscrowState.FUNDED.value
            assert source.balance == 10
            assert deep_reconcile_value_truth(session).matched

        # Two concurrent identical FUND requests may execute once and replay once.
        with Session.begin() as session:
            session.execute(text("DELETE FROM gerchain_ledger_movements"))
            session.execute(text("DELETE FROM gerchain_transaction_witnesses"))
            session.execute(text("DELETE FROM gerchain_outbox_events"))
            session.execute(text("DELETE FROM gerchain_idempotency_records"))
            session.execute(text("DELETE FROM gerchain_ledger_accounts"))
            session.execute(text("DELETE FROM escrows"))
        runtime.create_escrow(
            escrow_id="eai-concurrency", sender="CC-SOURCE", beneficiary="CC-BEN",
            refund_destination="CC-SOURCE", amount=40, currency="USD", condition="concurrency"
        )
        runtime.create_account("CC-SOURCE", initial_balance=100)
        runtime.create_account("eai-concurrency", initial_balance=0)

        def concurrent_fund():
            with Session() as session:
                try:
                    result = fund_escrow_in_transaction(
                        session, transaction_id="cc-fund", escrow_id="eai-concurrency",
                        source="CC-SOURCE", amount=40, currency="USD",
                    )
                    session.commit()
                    return result
                except Exception:
                    session.rollback()
                    raise

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: concurrent_fund(), range(2)))
        assert sorted(r["replayed"] for r in results) == [False, True]

        with Session() as session:
            source = session.get(LedgerAccountModel, "CC-SOURCE")
            escrow_account = session.get(LedgerAccountModel, "eai-concurrency")
            escrow = session.get(CanonicalEscrow, "eai-concurrency")
            assert source.balance == 60
            assert escrow_account.balance == 40
            assert escrow.state == EscrowState.FUNDED.value
            assert session.query(LedgerMovementModel).count() == 1
            assert deep_reconcile_value_truth(session).matched
    finally:
        engine.dispose()

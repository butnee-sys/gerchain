from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import TransactionWitness
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxEvent
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def _factory():
    url = os.environ.get("GERCHAIN_TEST_DATABASE_URL", os.environ["GERCHAIN_DATABASE_URL"])
    return ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="esc-prod",
            amount=100,
            currency="USD",
            witness_id="wit-prod",
        )
    )


def _reset_database(factory):
    with factory.engine.begin() as connection:
        connection.exec_driver_sql(
            "TRUNCATE TABLE "
            "gerchain_ledger_movements, gerchain_ledger_accounts, "
            "escrows, gerchain_transaction_witnesses, "
            "gerchain_outbox_events, gerchain_idempotency_records "
            "RESTART IDENTITY CASCADE"
        )


def _seed_escrow(session, escrow_id, *, amount=100, refund_destination="SRC"):
    now = datetime.now(timezone.utc)
    session.add(
        CanonicalEscrow(
            id=escrow_id,
            sender_address="SRC",
            receiver_address="DST",
            amount=amount,
            state=EscrowState.CREATED.value,
            condition_desc="production-test",
            refund_destination=refund_destination,
            currency="USD",
            version=0,
            created_at=now,
            updated_at=now,
        )
    )


def test_real_postgresql_factory_and_value_truth():
    factory = _factory()
    runtime = factory.create()
    _reset_database(factory)
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative
    assert runtime._canonical_ledger is not None

    with factory.session_factory() as session:
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "SRC", "USD", 500)
        PostgreSQLAtomicLedger.create_account_in_transaction(session, "DST", "USD", 0)
        _seed_escrow(session, "esc-prod", amount=100)
        session.commit()

    with factory.session_factory() as session:
        from persistence.fund_escrow import fund_escrow_in_transaction
        fund_escrow_in_transaction(
            session, transaction_id="tx-fund", escrow_id="esc-prod",
            source="SRC", amount=100, currency="USD"
        )
        session.commit()

    with factory.session_factory() as session:
        from persistence.lock_escrow import lock_escrow_in_transaction
        lock_escrow_in_transaction(session, transaction_id="tx-lock", escrow_id="esc-prod")
        session.commit()

    with factory.session_factory() as session:
        from persistence.release_escrow import release_escrow_in_transaction
        release_escrow_in_transaction(
            session, transaction_id="tx-release", escrow_id="esc-prod",
            beneficiary="DST", amount=100, currency="USD",
            decision_status="APPROVE", authorization_status="AUTHORIZED",
            trust=True, transparency=True, performance=True, evidence_verified=True
        )
        session.commit()

    with factory.session_factory() as session:
        src = session.execute(select(LedgerAccountModel).where(LedgerAccountModel.account_id == "SRC")).scalar_one()
        dst = session.execute(select(LedgerAccountModel).where(LedgerAccountModel.account_id == "DST")).scalar_one()
        escrow = session.execute(select(CanonicalEscrow).where(CanonicalEscrow.id == "esc-prod")).scalar_one()
        report = deep_reconcile_value_truth(session)
        assert src.balance == 400
        assert dst.balance == 100
        assert escrow.state == EscrowState.RELEASED.value
        assert report.matched
        assert session.execute(select(TransactionWitness)).scalars().all()
        assert session.execute(select(OutboxEvent)).scalars().all()
    factory.engine.dispose()


def test_production_factory_repairs_legacy_escrow_state_constraint():
    factory = _factory()
    factory.create()
    with factory.engine.begin() as connection:
        connection.execute(text("ALTER TABLE escrows DROP CONSTRAINT IF EXISTS ck_escrows_canonical_state"))
        connection.execute(text(
            "ALTER TABLE escrows ADD CONSTRAINT legacy_escrow_state_check "
            "CHECK (state IN ('CREATED','LOCKED','RELEASED'))"
        ))

    # Regression proof: create_all() alone cannot repair an existing table.
    # Production boot must apply the canonical migration and replace the stale
    # lifecycle constraint with the full six-state state machine.
    factory.create()
    with factory.engine.connect() as connection:
        constraints = connection.execute(text(
            "SELECT conname, pg_get_constraintdef(oid) AS definition "
            "FROM pg_constraint WHERE conrelid = 'escrows'::regclass "
            "AND contype = 'c' AND pg_get_constraintdef(oid) LIKE '%state%' "
        )).all()
        names = {row[0] for row in constraints}
        assert "ck_escrows_canonical_state" in names
        assert "legacy_escrow_state_check" not in names
        definition = next(row[1] for row in constraints if row[0] == "ck_escrows_canonical_state")
        assert "FUNDED" in definition
        assert "REFUNDED" in definition
        assert "CANCELLED" in definition
    factory.engine.dispose()

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel, PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import WitnessBase, TransactionWitness
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase, CanonicalEscrow, EscrowState
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.create_escrow import create_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory
from persistence.cancel_escrow import cancel_escrow_in_transaction
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.settlement_coordinator import SettlementCoordinator
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from postgres.migrations import _canonical_migration_files, checksum
from pathlib import Path
from sqlalchemy import text


@pytest.mark.postgres
def test_production_postgres_factory_and_canonical_value_flow():
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

    # Prove the runtime boot used the actual canonical migration runner and the
    # repository's exact 17-file migration chain, rather than metadata.create_all
    # alone. This assertion runs against the real PostgreSQL service in CI.
    migration_dir = Path(__file__).resolve().parents[2] / "postgres" / "migrations"
    canonical_files = _canonical_migration_files(migration_dir)
    assert [int(path.name.split("_", 1)[0]) for path in canonical_files] == list(range(1, 18))
    expected_checksums = {
        int(path.name.split("_", 1)[0]): checksum(path.read_text(encoding="utf-8"))
        for path in canonical_files
    }
    with engine.connect() as connection:
        applied_rows = connection.execute(
            text("SELECT version, checksum FROM schema_version ORDER BY version")
        ).all()
    applied_checksums = {int(version): digest for version, digest in applied_rows}
    assert list(applied_checksums) == list(range(1, 18)), applied_checksums
    assert applied_checksums == expected_checksums, {
        "expected": expected_checksums,
        "applied": applied_checksums,
    }

    for base in (AtomicLedgerBase, EscrowBase, OutboxBase, IdempotencyBase, WitnessBase):
        base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)
    with Session() as session:
        accounts = [
            ("pg-fund-source", 100), ("pg-release-escrow", 0), ("pg-release-beneficiary", 0),
            ("pg-refund-source", 100), ("pg-refund-escrow", 0),
            ("pg-cancel-source", 75), ("pg-cancel-escrow", 0),
            ("pg-settle-source", 50), ("pg-settle-destination", 0),
        ]
        for account_id, balance in accounts:
            session.add(LedgerAccountModel(account_id=account_id, currency="MNT", balance=balance, version=0, updated_at=now))
        session.add_all([
            CanonicalEscrow(id="pg-refund-escrow", sender_address="pg-refund-source", receiver_address="pg-refund-source", refund_destination="pg-refund-source", amount=100, state=EscrowState.CREATED.value, condition_desc="postgres-refund", currency="MNT", version=0, created_at=now, updated_at=now),
            CanonicalEscrow(id="pg-cancel-escrow", sender_address="pg-cancel-source", receiver_address="pg-cancel-source", refund_destination="pg-cancel-source", amount=75, state=EscrowState.CREATED.value, condition_desc="postgres-cancel", currency="MNT", version=0, created_at=now, updated_at=now),
        ])
        create_result = create_escrow_in_transaction(
            session,
            transaction_id="pg-create-tx",
            escrow_id="pg-release-escrow",
            source="pg-fund-source",
            beneficiary="pg-release-beneficiary",
            refund_destination="pg-fund-source",
            amount=100,
            currency="MNT",
            condition="postgres-release",
        )
        assert create_result["state"] == EscrowState.CREATED.value
        assert create_result["value_movement"] is False
        session.commit()

        fund_escrow_in_transaction(session, transaction_id="pg-fund-tx", escrow_id="pg-release-escrow", source="pg-fund-source", amount=100, currency="MNT")
        # Same operation/key/payload replay must be a no-op: no second ledger movement.
        fund_escrow_in_transaction(session, transaction_id="pg-fund-tx", escrow_id="pg-release-escrow", source="pg-fund-source", amount=100, currency="MNT")
        lock_escrow_in_transaction(session, transaction_id="pg-lock-tx", escrow_id="pg-release-escrow")
        release_escrow_in_transaction(session, transaction_id="pg-release-tx", escrow_id="pg-release-escrow", beneficiary="pg-release-beneficiary", amount=100, currency="MNT", decision_status="APPROVE", authorization_status="AUTHORIZED", trust=True, transparency=True, performance=True, evidence_verified=True)

        fund_escrow_in_transaction(session, transaction_id="pg-refund-fund-tx", escrow_id="pg-refund-escrow", source="pg-refund-source", amount=100, currency="MNT")
        lock_escrow_in_transaction(session, transaction_id="pg-refund-lock-tx", escrow_id="pg-refund-escrow")
        refund_escrow_in_transaction(session, transaction_id="pg-refund-tx", escrow_id="pg-refund-escrow", amount=100, currency="MNT")

        fund_escrow_in_transaction(session, transaction_id="pg-cancel-fund-tx", escrow_id="pg-cancel-escrow", source="pg-cancel-source", amount=75, currency="MNT")
        cancel_escrow_in_transaction(session, transaction_id="pg-cancel-tx", escrow_id="pg-cancel-escrow")

        SettlementCoordinator(session).settle_in_transaction(transaction_id="pg-settlement-tx", source="pg-settle-source", destination="pg-settle-destination", amount=25, currency="MNT")
        session.commit()

        escrows = {row.id: row.state for row in session.execute(select(CanonicalEscrow).where(CanonicalEscrow.id.in_(["pg-release-escrow", "pg-refund-escrow", "pg-cancel-escrow"]))).scalars()}
        balances = {row.account_id: row.balance for row in session.execute(select(LedgerAccountModel)).scalars() if row.account_id.startswith("pg-")}
        movements = session.execute(select(LedgerMovementModel)).scalars().all()
        witnesses = session.execute(select(TransactionWitness)).scalars().all()
        outbox = session.execute(select(OutboxEvent)).scalars().all()
        report = deep_reconcile_value_truth(session)

        assert escrows == {"pg-release-escrow": EscrowState.RELEASED.value, "pg-refund-escrow": EscrowState.REFUNDED.value, "pg-cancel-escrow": EscrowState.CANCELLED.value}
        assert balances["pg-fund-source"] == 0
        assert balances["pg-release-beneficiary"] == 100
        assert balances["pg-refund-source"] == 100
        assert balances["pg-cancel-source"] == 75
        assert balances["pg-settle-source"] == 25
        assert balances["pg-settle-destination"] == 25
        assert len(movements) == 7
        assert session.query(TransactionWitness).filter_by(transaction_id="pg-create-tx", event_type="GERCHAIN_CREATED", amount=0).count() == 1
        assert session.query(OutboxEvent).filter_by(event_type="GERCHAIN_CREATED", aggregate_id="pg-release-escrow").count() == 1
        assert {m.operation for m in movements} == {"FUND", "RELEASE", "REFUND", "CANCEL", "SETTLEMENT"}
        assert {w.event_type for w in witnesses} >= {"GERCHAIN_FUNDED", "GERCHAIN_LOCKED", "GERCHAIN_RELEASED", "GERCHAIN_REFUNDED", "GERCHAIN_CANCELLED", "GERCHAIN_SETTLED"}
        assert {e.event_type for e in outbox} >= {"GERCHAIN_FUNDED", "GERCHAIN_LOCKED", "GERCHAIN_RELEASED", "GERCHAIN_REFUNDED", "GERCHAIN_CANCELLED", "GERCHAIN_SETTLED"}
        assert report.matched, report.issues
        assert report.canonical_movement_count == 7

    engine.dispose()



@pytest.mark.postgres
def test_postgres_create_rollback_leaves_no_partial_canonical_evidence():
    """A failed caller transaction must roll back CREATE truth and every evidence row."""
    import uuid

    url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="pg-create-rollback-bootstrap",
            amount=10,
            currency="MNT",
            witness_id="pg-create-rollback-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()
    assert runtime.is_canonical_ledger_authoritative

    Session = sessionmaker(bind=engine, expire_on_commit=False)
    suffix = uuid.uuid4().hex
    transaction_id = f"pg-create-rollback-tx-{suffix}"
    escrow_id = f"pg-create-rollback-escrow-{suffix}"
    try:
        with Session() as session:
            try:
                with session.begin():
                    result = create_escrow_in_transaction(
                        session,
                        transaction_id=transaction_id,
                        escrow_id=escrow_id,
                        source=f"source-{suffix}",
                        beneficiary=f"beneficiary-{suffix}",
                        refund_destination=f"source-{suffix}",
                        amount=10,
                        currency="MNT",
                        condition="rollback proof",
                    )
                    assert result["state"] == EscrowState.CREATED.value
                    assert result["value_movement"] is False
                    raise RuntimeError("intentional rollback probe")
            except RuntimeError as exc:
                assert str(exc) == "intentional rollback probe"

        with Session() as session:
            assert session.get(CanonicalEscrow, escrow_id) is None
            assert session.execute(
                select(TransactionWitness).where(TransactionWitness.transaction_id == transaction_id)
            ).scalar_one_or_none() is None
            assert session.execute(
                select(OutboxEvent).where(OutboxEvent.event_id == f"gerchain_created:{transaction_id}")
            ).scalar_one_or_none() is None
            from persistence.durable_idempotency import DurableIdempotencyRecord
            assert session.execute(
                select(DurableIdempotencyRecord).where(DurableIdempotencyRecord.key == transaction_id)
            ).scalar_one_or_none() is None
    finally:
        engine.dispose()


@pytest.mark.postgres
def test_postgres_restart_recovery_preserves_canonical_truth_and_idempotency():
    """A fresh runtime/engine after restart must recover state without duplicate movement."""
    import uuid

    url = os.environ["GERCHAIN_DATABASE_URL"]
    suffix = uuid.uuid4().hex
    escrow_id = f"pg-restart-escrow-{suffix}"
    source_id = f"pg-restart-source-{suffix}"
    tx_id = f"pg-restart-fund-{suffix}"
    amount = 10

    engine = create_engine(url, pool_pre_ping=True)
    config = ProductionRuntimeConfig(
        database_url=url,
        escrow_id=escrow_id,
        amount=amount,
        currency="MNT",
        witness_id=f"pg-restart-witness-{suffix}",
    )
    try:
        runtime = ProductionRuntimeFactory(config, engine=engine).create()
        assert runtime.is_canonical_ledger_authoritative
        Session = sessionmaker(bind=engine, expire_on_commit=False)
        with Session() as session:
            now = datetime.now(timezone.utc)
            session.add(LedgerAccountModel(
                account_id=source_id, currency="MNT", balance=amount,
                version=0, updated_at=now,
            ))
            session.commit()
            create_escrow_in_transaction(
                session,
                transaction_id=f"pg-restart-create-{suffix}",
                escrow_id=escrow_id,
                source=source_id,
                beneficiary=f"pg-restart-beneficiary-{suffix}",
                refund_destination=source_id,
                amount=amount,
                currency="MNT",
                condition="restart recovery proof",
            )
            session.commit()
            fund_escrow_in_transaction(
                session, transaction_id=tx_id, escrow_id=escrow_id,
                source=source_id, amount=amount, currency="MNT",
            )
            session.commit()
            assert session.get(CanonicalEscrow, escrow_id).state == EscrowState.FUNDED.value
            before_movements = session.query(LedgerMovementModel).filter_by(transaction_id=tx_id).count()
            assert before_movements == 1
    finally:
        engine.dispose()

    # Simulate process restart: discard engine/session/runtime and rebuild them.
    restarted_engine = create_engine(url, pool_pre_ping=True)
    try:
        restarted_runtime = ProductionRuntimeFactory(config, engine=restarted_engine).create()
        assert restarted_runtime.is_canonical_ledger_authoritative
        RestartedSession = sessionmaker(bind=restarted_engine, expire_on_commit=False)
        with RestartedSession() as session:
            recovered = session.get(CanonicalEscrow, escrow_id)
            assert recovered is not None
            assert recovered.state == EscrowState.FUNDED.value
            assert session.get(LedgerAccountModel, source_id).balance == 0

            replay = fund_escrow_in_transaction(
                session, transaction_id=tx_id, escrow_id=escrow_id,
                source=source_id, amount=amount, currency="MNT",
            )
            session.commit()
            assert replay.get("idempotent_replay") is True or replay.get("replayed") is True

            movement_count = session.query(LedgerMovementModel).filter_by(transaction_id=tx_id).count()
            assert movement_count == 1
            report = deep_reconcile_value_truth(session)
            assert report.matched, report.issues
    finally:
        restarted_engine.dispose()

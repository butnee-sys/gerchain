"""PostgreSQL end-to-end proof for canonical escrow/value-flow operations.

Requires GERCHAIN_TEST_DATABASE_URL pointing at a disposable PostgreSQL database.
The test applies the exact canonical 16-migration chain, executes all required
operations using the real SQLAlchemy/PostgreSQL boundary, then reconciles the
persisted movement/evidence graph. It intentionally never truncates shared data.
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from pathlib import Path

import psycopg
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel, PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import TransactionWitness
from persistence.cancel_escrow import cancel_escrow_in_transaction
from persistence.deep_value_reconciliation import deep_reconcile_value_truth
from persistence.durable_idempotency import DurableIdempotencyRecord, IdempotencyBase
from persistence.escrow_aggregate import EscrowBase, CanonicalEscrow, create_escrow_in_transaction
from persistence.fund_escrow import fund_escrow_in_transaction
from persistence.lock_escrow import lock_escrow_in_transaction
from persistence.recovery_outbox import OutboxBase, OutboxEvent
from persistence.refund_escrow import refund_escrow_in_transaction
from persistence.release_escrow import release_escrow_in_transaction
from persistence.settlement_coordinator import SettlementCoordinator


@pytest.fixture()
def pg_factory():
    url = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is not configured")
    driver_url = url.replace("postgresql+psycopg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )
    with psycopg.connect(driver_url) as connection:
        from postgres.migrations import apply_migrations
        apply_migrations(connection, Path("postgres/migrations"))
        rows = connection.execute(
            "SELECT version, checksum FROM schema_version ORDER BY version"
        ).fetchall()
        assert [row[0] for row in rows] == list(range(1, 17)), rows
        assert all(row[1] for row in rows), rows

    engine = create_engine(url, pool_pre_ping=True)
    # Migrations are authoritative; create_all only fills tables absent from the
    # migration set so ORM-only evidence models remain available during diagnosis.
    for base in (AtomicLedgerBase, EscrowBase, OutboxBase, IdempotencyBase, TransactionWitness):
        base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        engine.dispose()


def test_postgres_14_migrations_and_full_value_flow_reconcile(pg_factory):
    suffix = uuid.uuid4().hex[:12]
    currency = "MNT"
    amount = 100
    source = f"src-{suffix}"
    beneficiary = f"ben-{suffix}"
    settlement_source = f"settle-src-{suffix}"
    settlement_destination = f"settle-dst-{suffix}"
    release_id = f"esc-release-{suffix}"
    refund_id = f"esc-refund-{suffix}"
    cancel_funded_id = f"esc-cancel-funded-{suffix}"
    cancel_created_id = f"esc-cancel-created-{suffix}"

    with pg_factory() as session:
        for account_id, balance in (
            (source, 1000),
            (beneficiary, 0),
            (settlement_source, 500),
            (settlement_destination, 0),
            (release_id, 0),
            (refund_id, 0),
            (cancel_funded_id, 0),
        ):
            PostgreSQLAtomicLedger.create_account_in_transaction(
                session, account_id, currency, balance
            )

        for escrow_id in (release_id, refund_id, cancel_funded_id, cancel_created_id):
            create_escrow_in_transaction(
                session,
                escrow_id=escrow_id,
                sender=source,
                beneficiary=beneficiary,
                refund_destination=source,
                amount=amount,
                currency=currency,
                condition="EA-35 PostgreSQL re-performance",
            )
        session.commit()

    account_ids = [source, beneficiary, settlement_source, settlement_destination,
                   release_id, refund_id, cancel_funded_id]
    with pg_factory() as session:
        opening_balances = {
            row.account_id: {"currency": row.currency, "balance": int(row.balance), "version": row.version}
            for row in session.execute(
                select(LedgerAccountModel).where(LedgerAccountModel.account_id.in_(account_ids))
            ).scalars()
        }
    assert len(opening_balances) == len(account_ids)

    # CREATE -> FUND -> LOCK -> RELEASE.
    with pg_factory() as session:
        fund_escrow_in_transaction(
            session, transaction_id=f"fund-release-{suffix}", escrow_id=release_id,
            source=source, amount=amount, currency=currency,
        )
        session.commit()
    with pg_factory() as session:
        lock_escrow_in_transaction(
            session, transaction_id=f"lock-release-{suffix}", escrow_id=release_id,
        )
        session.commit()
    with pg_factory() as session:
        release_escrow_in_transaction(
            session, transaction_id=f"release-{suffix}", escrow_id=release_id,
            beneficiary=beneficiary, amount=amount, currency=currency,
            decision_status="APPROVE", authorization_status="AUTHORIZED",
            trust=True, transparency=True, performance=True, evidence_verified=True,
        )
        session.commit()

    # REFUND is independently exercised from LOCKED and uses the authoritative
    # refund destination stored in the escrow aggregate.
    with pg_factory() as session:
        fund_escrow_in_transaction(
            session, transaction_id=f"fund-refund-{suffix}", escrow_id=refund_id,
            source=source, amount=amount, currency=currency,
        )
        session.commit()
    with pg_factory() as session:
        lock_escrow_in_transaction(
            session, transaction_id=f"lock-refund-{suffix}", escrow_id=refund_id,
        )
        session.commit()
    with pg_factory() as session:
        refund_escrow_in_transaction(
            session, transaction_id=f"refund-{suffix}", escrow_id=refund_id,
            amount=amount, currency=currency,
        )
        session.commit()

    # CANCEL covers both a FUNDED reversal and a CREATED state-only cancellation.
    with pg_factory() as session:
        fund_escrow_in_transaction(
            session, transaction_id=f"fund-cancel-{suffix}", escrow_id=cancel_funded_id,
            source=source, amount=amount, currency=currency,
        )
        session.commit()
    with pg_factory() as session:
        cancel_escrow_in_transaction(
            session, transaction_id=f"cancel-funded-{suffix}", escrow_id=cancel_funded_id,
        )
        session.commit()
    with pg_factory() as session:
        cancel_escrow_in_transaction(
            session, transaction_id=f"cancel-created-{suffix}", escrow_id=cancel_created_id,
        )
        session.commit()

    # SETTLEMENT uses the same canonical Ledger movement/evidence boundary.
    with pg_factory() as session:
        SettlementCoordinator(session).settle_in_transaction(
            transaction_id=f"settlement-{suffix}",
            source=settlement_source,
            destination=settlement_destination,
            amount=25,
            currency=currency,
        )
        session.commit()

    with pg_factory() as session:
        report = deep_reconcile_value_truth(session)
        assert report.matched, [issue.__dict__ for issue in report.issues]

        tx_ids = [
            f"fund-release-{suffix}", f"lock-release-{suffix}", f"release-{suffix}",
            f"fund-refund-{suffix}", f"lock-refund-{suffix}", f"refund-{suffix}",
            f"fund-cancel-{suffix}", f"cancel-funded-{suffix}",
            f"cancel-created-{suffix}", f"settlement-{suffix}",
        ]
        movements = list(session.execute(
            select(LedgerMovementModel).where(LedgerMovementModel.transaction_id.in_(tx_ids))
        ).scalars())
        movement_tx_ids = [movement.transaction_id for movement in movements]
        assert len(movement_tx_ids) == len(set(movement_tx_ids))
        assert set(movement_tx_ids) == {
            f"fund-release-{suffix}", f"release-{suffix}",
            f"fund-refund-{suffix}", f"refund-{suffix}",
            f"fund-cancel-{suffix}", f"cancel-funded-{suffix}",
            f"settlement-{suffix}",
        }
        assert len(movements) == 7, movement_tx_ids

        state_only_tx_ids = {f"lock-release-{suffix}", f"lock-refund-{suffix}", f"cancel-created-{suffix}"}
        assert not state_only_tx_ids.intersection(movement_tx_ids)

        escrow_states = {
            row.id: row.state
            for row in session.execute(
                select(CanonicalEscrow).where(
                    CanonicalEscrow.id.in_((release_id, refund_id, cancel_funded_id, cancel_created_id))
                )
            ).scalars()
        }
        assert escrow_states == {
            release_id: "RELEASED",
            refund_id: "REFUNDED",
            cancel_funded_id: "CANCELLED",
            cancel_created_id: "CANCELLED",
        }

        # Replaying a committed movement must not create a second movement.
        before_count = len(movements)
        replay = fund_escrow_in_transaction(
            session, transaction_id=f"fund-release-{suffix}", escrow_id=release_id,
            source=source, amount=amount, currency=currency,
        )
        assert replay.get("replayed") is True
        session.commit()
        after_count = len(list(session.execute(
            select(LedgerMovementModel).where(LedgerMovementModel.transaction_id.in_(tx_ids))
        ).scalars()))
        assert after_count == before_count

        final_report = deep_reconcile_value_truth(session)
        assert final_report.matched, [issue.__dict__ for issue in final_report.issues]

        closing_balances = {
            row.account_id: {"currency": row.currency, "balance": int(row.balance), "version": row.version}
            for row in session.execute(
                select(LedgerAccountModel).where(LedgerAccountModel.account_id.in_(account_ids))
            ).scalars()
        }
        movement_rows = list(session.execute(
            select(LedgerMovementModel).where(LedgerMovementModel.transaction_id.in_(tx_ids))
        ).scalars())
        witness_rows = list(session.execute(
            select(TransactionWitness).where(TransactionWitness.transaction_id.in_(tx_ids))
        ).scalars())
        idempotency_rows = list(session.execute(
            select(DurableIdempotencyRecord).where(DurableIdempotencyRecord.key.in_(tx_ids))
        ).scalars())
        outbox_rows = list(session.execute(
            select(OutboxEvent).where(OutboxEvent.event_id.like(f"%{suffix}%"))
        ).scalars())
        migration_rows = session.execute(
            text("SELECT version, checksum, applied_at::text FROM schema_version ORDER BY version")
        ).all()
        assert len(movement_rows) == 7
        assert len(witness_rows) == 10
        assert len(outbox_rows) == 10
        assert len(idempotency_rows) == 10
        assert all(row.state == "COMPLETED" for row in idempotency_rows)

        evidence = {
            "status": "PASS",
            "commit_sha": os.environ.get("GITHUB_SHA", "UNSET"),
            "database": session.get_bind().url.database,
            "migration_history": [
                {"version": row.version, "checksum": row.checksum, "applied_at": row.applied_at}
                for row in migration_rows
            ],
            "migration_count": len(migration_rows),
            "currency": currency,
            "test_suffix": suffix,
            "opening_balances": opening_balances,
            "closing_balances": closing_balances,
            "movement_count": len(movement_rows),
            "movements": [
                {"transaction_id": row.transaction_id, "operation": row.operation,
                 "escrow_id": row.escrow_id, "source": row.source,
                 "destination": row.destination, "amount": int(row.amount),
                 "currency": row.currency, "integrity_hash": row.integrity_hash}
                for row in movement_rows
            ],
            "witness_count": len(witness_rows),
            "witnesses": [
                {"transaction_id": row.transaction_id, "event_type": row.event_type,
                 "escrow_id": row.escrow_id, "amount": int(row.amount)}
                for row in witness_rows
            ],
            "outbox_count": len(outbox_rows),
            "outbox": [
                {"event_id": row.event_id, "event_type": row.event_type,
                 "aggregate_id": row.aggregate_id, "state": row.state}
                for row in outbox_rows
            ],
            "idempotency_count": len(idempotency_rows),
            "idempotency": [
                {"key": row.key, "fingerprint": row.fingerprint, "state": row.state}
                for row in idempotency_rows
            ],
            "reconciliation": {
                "matched": final_report.matched,
                "canonical_movement_count": final_report.canonical_movement_count,
                "witness_count": final_report.witness_count,
                "outbox_count": final_report.outbox_count,
                "idempotency_count": final_report.idempotency_count,
                "escrow_count": final_report.escrow_count,
                "issues": [issue.__dict__ for issue in final_report.issues],
            },
            "duplicate_movements": 0,
            "replay_created_no_new_movement": after_count == before_count,
        }
        evidence_dir = Path(os.environ.get("GERCHAIN_EVIDENCE_DIR", "artifacts/ea35"))
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = evidence_dir / "postgres-value-flow-evidence.json"
        evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\\n", encoding="utf-8")
        print(f"POSTGRES_VALUE_FLOW_EVIDENCE={evidence_path}")
        print(
            "EA35_POSTGRES_LIFECYCLE=PASS "
            f"migration_versions={len(migration_rows)} movement_count={len(movement_rows)} "
            f"witness_count={len(witness_rows)} outbox_count={len(outbox_rows)} "
            f"idempotency_count={len(idempotency_rows)} reconciliation_issues={len(final_report.issues)}"
        )

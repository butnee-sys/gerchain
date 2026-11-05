"""PostgreSQL end-to-end proof for canonical escrow/value-flow operations.

Requires GERCHAIN_TEST_DATABASE_URL pointing at a disposable PostgreSQL database.
The test applies the exact canonical 18-migration chain, executes all required
operations using the real SQLAlchemy/PostgreSQL boundary, then reconciles the
persisted movement/evidence graph. It intentionally never truncates shared data.
"""
from __future__ import annotations

import json
import base64
import os
import uuid
from pathlib import Path

import psycopg
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, LedgerMovementModel, PostgreSQLAtomicLedger
from persistence.signed_change_authorization import (
    SignedChangeAuthorization, canonical_release_payload, canonical_refund_payload, canonical_payload_hash,
)
from dee_security.root_of_trust import RootOfTrust, SignedChange
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



def _signed_authorization(*, operation, transaction_id, escrow_id, destination, amount, currency, evidence, monkeypatch):
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    public_key_b64 = base64.b64encode(public_key).decode("ascii")
    owner_id = "gerchain-postgres-eai-test-owner"
    monkeypatch.setenv("GERCHAIN_AUTH_OWNER_ID", owner_id)
    monkeypatch.setenv("GERCHAIN_AUTH_PUBLIC_KEY_B64", public_key_b64)
    root = RootOfTrust(owner_id=owner_id, public_key_b64=public_key_b64)

    if operation == "RELEASE":
        protected_payload = canonical_release_payload(
            transaction_id=transaction_id, escrow_id=escrow_id,
            source=escrow_id, destination=destination, amount=amount,
            currency=currency, decision_status="APPROVE", trust=True,
            transparency=True, performance=True, evidence_verified=True,
            evidence=evidence,
        )
    elif operation == "REFUND":
        protected_payload = canonical_refund_payload(
            transaction_id=transaction_id, escrow_id=escrow_id,
            source=escrow_id, destination=destination, amount=amount,
            currency=currency, authorized=True, transparency=True,
            dispute_or_cancellation_verified=True, evidence=evidence,
        )
    else:
        raise ValueError(f"unsupported test authorization operation: {operation}")

    unsigned = SignedChange(
        owner_id=owner_id, change_id=f"CHANGE-{transaction_id}", version=1,
        payload_hash=canonical_payload_hash(protected_payload), signature="",
    )
    signing_bytes = json.dumps(
        unsigned.signing_payload(), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    signed_change = SignedChange(
        owner_id=owner_id, change_id=unsigned.change_id, version=1,
        payload_hash=unsigned.payload_hash,
        signature=base64.b64encode(private_key.sign(signing_bytes)).decode("ascii"),
    )
    return root, signed_change, owner_id


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
        assert [row[0] for row in rows] == list(range(1, 19)), rows
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


def test_postgres_18_migrations_and_full_value_flow_reconcile(pg_factory, monkeypatch):
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
    release_tx_id = f"release-{suffix}"
    release_evidence = {"decision_record": f"approved-{suffix}"}
    release_root, release_change, release_owner = _signed_authorization(
        operation="RELEASE", transaction_id=release_tx_id, escrow_id=release_id,
        destination=beneficiary, amount=amount, currency=currency,
        evidence=release_evidence, monkeypatch=monkeypatch,
    )
    with pg_factory() as session:
        release_escrow_in_transaction(
            session, transaction_id=release_tx_id, escrow_id=release_id,
            beneficiary=beneficiary, amount=amount, currency=currency,
            decision_status="APPROVE", root=release_root,
            signed_change=release_change, owner_id=release_owner,
            trust=True, transparency=True, performance=True, evidence_verified=True,
            payload={"evidence": release_evidence},
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
    refund_tx_id = f"refund-{suffix}"
    refund_evidence = {"case_record": f"verified-cancellation-{suffix}"}
    refund_root, refund_change, refund_owner = _signed_authorization(
        operation="REFUND", transaction_id=refund_tx_id, escrow_id=refund_id,
        destination=source, amount=amount, currency=currency,
        evidence=refund_evidence, monkeypatch=monkeypatch,
    )
    with pg_factory() as session:
        refund_escrow_in_transaction(
            session, transaction_id=refund_tx_id, escrow_id=refund_id,
            amount=amount, currency=currency, root=refund_root,
            signed_change=refund_change, owner_id=refund_owner,
            authorized=True, transparency=True,
            dispute_or_cancellation_verified=True,
            payload={"evidence": refund_evidence},
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
        authorization_rows = list(session.execute(
            select(SignedChangeAuthorization).where(
                SignedChangeAuthorization.transaction_id.in_((release_tx_id, refund_tx_id))
            )
        ).scalars())
        assert len(authorization_rows) == 2
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
            "signed_authorization_count": len(authorization_rows),
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
        evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True, default=str) + "
", encoding="utf-8")
        print(f"POSTGRES_VALUE_FLOW_EVIDENCE={evidence_path}")
        print(
            "EA35_POSTGRES_LIFECYCLE=PASS "
            f"migration_versions={len(migration_rows)} movement_count={len(movement_rows)} "
            f"witness_count={len(witness_rows)} outbox_count={len(outbox_rows)} "
            f"idempotency_count={len(idempotency_rows)} reconciliation_issues={len(final_report.issues)}"
        )


def test_postgres_release_and_refund_authorization_roll_back_with_failed_value_transfer(pg_factory, monkeypatch):
    """Authorization and every value/evidence write must roll back on PostgreSQL."""
    suffix = uuid.uuid4().hex[:12]
    source = f"rollback-src-{suffix}"
    beneficiary = f"rollback-ben-{suffix}"
    amount = 100
    currency = "MNT"
    cases = {
        "RELEASE": {
            "escrow_id": f"rollback-release-{suffix}",
            "transaction_id": f"rollback-release-tx-{suffix}",
        },
        "REFUND": {
            "escrow_id": f"rollback-refund-{suffix}",
            "transaction_id": f"rollback-refund-tx-{suffix}",
        },
    }

    with pg_factory() as session:
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, source, currency, 1000
        )
        PostgreSQLAtomicLedger.create_account_in_transaction(
            session, beneficiary, currency, 0
        )
        for operation, case in cases.items():
            escrow_id = case["escrow_id"]
            create_escrow_in_transaction(
                session,
                escrow_id=escrow_id,
                sender=source,
                beneficiary=beneficiary,
                refund_destination=source,
                amount=amount,
                currency=currency,
                condition=f"PostgreSQL {operation} rollback proof",
            )
            fund_escrow_in_transaction(
                session,
                transaction_id=f"fund-{case['transaction_id']}",
                escrow_id=escrow_id,
                source=source,
                amount=amount,
                currency=currency,
            )
            lock_escrow_in_transaction(
                session,
                transaction_id=f"lock-{case['transaction_id']}",
                escrow_id=escrow_id,
            )
        session.commit()

    def fail_ledger_transfer(*args, **kwargs):
        raise RuntimeError("injected PostgreSQL ledger transfer failure")

    for operation, case in cases.items():
        escrow_id = case["escrow_id"]
        transaction_id = case["transaction_id"]
        destination = beneficiary if operation == "RELEASE" else source
        evidence = {"rollback_case": operation, "nonce": suffix}
        root, signed_change, owner_id = _signed_authorization(
            operation=operation,
            transaction_id=transaction_id,
            escrow_id=escrow_id,
            destination=destination,
            amount=amount,
            currency=currency,
            evidence=evidence,
            monkeypatch=monkeypatch,
        )

        with pytest.raises(RuntimeError, match="injected PostgreSQL ledger transfer failure"):
            with pg_factory.begin() as session:
                if operation == "RELEASE":
                    release_escrow_in_transaction(
                        session,
                        transaction_id=transaction_id,
                        escrow_id=escrow_id,
                        beneficiary=beneficiary,
                        amount=amount,
                        currency=currency,
                        decision_status="APPROVE",
                        root=root,
                        signed_change=signed_change,
                        owner_id=owner_id,
                        trust=True,
                        transparency=True,
                        performance=True,
                        evidence_verified=True,
                        ledger_transfer=fail_ledger_transfer,
                        payload={"evidence": evidence},
                    )
                else:
                    refund_escrow_in_transaction(
                        session,
                        transaction_id=transaction_id,
                        escrow_id=escrow_id,
                        amount=amount,
                        currency=currency,
                        root=root,
                        signed_change=signed_change,
                        owner_id=owner_id,
                        authorized=True,
                        transparency=True,
                        dispute_or_cancellation_verified=True,
                        ledger_transfer=fail_ledger_transfer,
                        payload={"evidence": evidence},
                    )

        with pg_factory() as session:
            assert session.get(CanonicalEscrow, escrow_id).state == "LOCKED"
            assert session.get(LedgerAccountModel, escrow_id).balance == amount
            assert session.get(LedgerAccountModel, source).balance == 1000 - amount * 2
            assert session.get(LedgerAccountModel, beneficiary).balance == 0
            assert session.query(SignedChangeAuthorization).filter_by(
                transaction_id=transaction_id
            ).count() == 0
            assert session.query(LedgerMovementModel).filter_by(
                transaction_id=transaction_id
            ).count() == 0
            assert session.query(TransactionWitness).filter_by(
                transaction_id=transaction_id
            ).count() == 0
            assert session.query(DurableIdempotencyRecord).filter_by(
                key=transaction_id
            ).count() == 0
            assert session.query(OutboxEvent).filter(
                OutboxEvent.event_id.like(f"%{suffix}%")
            ).count() == 0

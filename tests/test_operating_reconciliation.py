from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from core.idempotency import IdempotencyEngine
from persistence.atomic_release import (
    ReleaseAccount,
    ReleaseEscrow,
    ReleaseOperation,
    ReleaseWitness,
    initialize_atomic_release_schema,
)
from persistence.reconciliation import reconcile_release_state
from persistence.recovery_outbox import OutboxEvent


def _factory():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    engine = create_engine(url, pool_pre_ping=True)
    initialize_atomic_release_schema(engine)
    return engine


def _seed_consistent(engine, prefix="RC"):
    now = datetime.now(timezone.utc)
    payload = {"transaction_id": f"{prefix}-TX", "escrow_id": f"{prefix}-ESC", "source": f"{prefix}-SRC", "destination": f"{prefix}-DST", "amount": 100}
    with Session(engine) as session:
        session.add_all([
            ReleaseAccount(account_id=f"{prefix}-SRC", balance=0, updated_at=now),
            ReleaseAccount(account_id=f"{prefix}-DST", balance=100, updated_at=now),
            ReleaseEscrow(escrow_id=f"{prefix}-ESC", state="RELEASED", amount=100, updated_at=now),
            ReleaseOperation(
                idempotency_key=f"{prefix}-KEY",
                fingerprint=IdempotencyEngine.fingerprint(payload),
                transaction_id=f"{prefix}-TX",
                escrow_id=f"{prefix}-ESC",
                destination=f"{prefix}-DST",
                amount=100,
                state="COMPLETED",
                result_json='{"event_id":"release:' + f"{prefix}-TX" + '","state":"RELEASED"}',
                created_at=now,
                updated_at=now,
            ),
            ReleaseWitness(transaction_id=f"{prefix}-TX", event_type="RELEASED", amount=100, created_at=now),
            OutboxEvent(
                event_id=f"release:{prefix}-TX",
                event_type="GERCHAIN_RELEASED",
                aggregate_id=f"{prefix}-TX",
                payload_json="{}",
                state="PENDING",
                lease_until=None,
                attempts=0,
                created_at=now,
                updated_at=now,
            ),
        ])
        session.commit()


def test_consistent_release_store_reconciles_green():
    engine = _factory()
    _seed_consistent(engine)
    with Session(engine) as session:
        report = reconcile_release_state(session)
    assert report.passed is True
    assert report.findings == ()


def test_released_without_witness_fails_closed():
    engine = _factory()
    _seed_consistent(engine, "RC2")
    with Session(engine) as session:
        session.query(ReleaseWitness).filter(ReleaseWitness.transaction_id == "RC2-TX").delete()
        session.commit()
        report = reconcile_release_state(session)
    assert report.passed is False
    assert any(f.code == "RC-WITNESS-MISSING" for f in report.findings)


def test_released_without_outbox_fails_closed():
    engine = _factory()
    _seed_consistent(engine, "RC3")
    with Session(engine) as session:
        session.query(OutboxEvent).filter(OutboxEvent.event_id == "release:RC3-TX").delete()
        session.commit()
        report = reconcile_release_state(session)
    assert report.passed is False
    assert any(f.code == "RC-OUTBOX-MISSING" for f in report.findings)


def test_locked_with_release_evidence_fails_closed():
    engine = _factory()
    _seed_consistent(engine, "RC4")
    with Session(engine) as session:
        session.query(ReleaseEscrow).filter(ReleaseEscrow.escrow_id == "RC4-ESC").update({"state": "LOCKED"})
        session.query(ReleaseOperation).filter(ReleaseOperation.idempotency_key == "RC4-KEY").update({"state": "PROCESSING"})
        session.commit()
        report = reconcile_release_state(session)
    assert report.passed is False
    assert any(f.code == "RC-LOCKED-WITH-EVIDENCE" for f in report.findings)


def test_stale_processing_is_reported_for_recovery():
    engine = _factory()
    now = datetime.now(timezone.utc)
    stale = now - timedelta(minutes=10)
    payload = {"transaction_id": "RC5-TX", "escrow_id": "RC5-ESC", "source": "RC5-SRC", "destination": "RC5-DST", "amount": 100}
    with Session(engine) as session:
        session.add_all([
            ReleaseAccount(account_id="RC5-SRC", balance=100, updated_at=now),
            ReleaseAccount(account_id="RC5-DST", balance=0, updated_at=now),
            ReleaseEscrow(escrow_id="RC5-ESC", state="LOCKED", amount=100, updated_at=stale),
            ReleaseOperation(idempotency_key="RC5-KEY", fingerprint=IdempotencyEngine.fingerprint(payload), transaction_id="RC5-TX", escrow_id="RC5-ESC", destination="RC5-DST", amount=100, state="PROCESSING", created_at=stale, updated_at=stale),
        ])
        session.commit()
        report = reconcile_release_state(session)
    assert report.passed is False
    assert any(f.code == "RC-STALE-PROCESSING" for f in report.findings)

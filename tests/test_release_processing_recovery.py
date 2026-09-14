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
    PostgreSQLAtomicRelease,
    initialize_atomic_release_schema,
)
from persistence.recovery_outbox import OutboxEvent


def _factory():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    engine = create_engine(url, pool_pre_ping=True)
    initialize_atomic_release_schema(engine)
    return engine


def _proof():
    return {"trust": True, "transparency": True, "performance": True}


def test_abandoned_processing_is_reclaimed_without_double_movement():
    engine = _factory()
    now = datetime.now(timezone.utc)
    stale = now - timedelta(minutes=10)
    with Session(engine) as session:
        session.add_all([
            ReleaseAccount(account_id="REC-SRC", balance=1000, updated_at=now),
            ReleaseAccount(account_id="REC-DST", balance=0, updated_at=now),
            ReleaseEscrow(escrow_id="REC-ESC", state="LOCKED", amount=1000, updated_at=now),
        ])
        payload = {"transaction_id": "REC-TX", "escrow_id": "REC-ESC", "source": "REC-SRC", "destination": "REC-DST", "amount": 1000}
        session.add(ReleaseOperation(
            idempotency_key="REC-KEY",
            fingerprint=IdempotencyEngine.fingerprint(payload),
            transaction_id="REC-TX",
            escrow_id="REC-ESC",
            destination="REC-DST",
            amount=1000,
            state="PROCESSING",
            created_at=stale,
            updated_at=stale,
        ))
        session.commit()

    release = PostgreSQLAtomicRelease(lambda: Session(engine), processing_lease_seconds=60)
    result = release.release(
        idempotency_key="REC-KEY",
        transaction_id="REC-TX",
        escrow_id="REC-ESC",
        source="REC-SRC",
        destination="REC-DST",
        amount=1000,
        decision_status="APPROVE",
        authorization_status="AUTHORIZED",
        trinity_proof=_proof(),
        evidence_verified=True,
    )

    assert result.replay is False
    with Session(engine) as session:
        assert session.get(ReleaseAccount, "REC-SRC").balance == 0
        assert session.get(ReleaseAccount, "REC-DST").balance == 1000
        assert session.get(ReleaseEscrow, "REC-ESC").state == "RELEASED"
        op = session.execute(select(ReleaseOperation).where(ReleaseOperation.idempotency_key == "REC-KEY")).scalar_one()
        assert op.state == "COMPLETED"
        assert len(session.execute(select(ReleaseWitness)).scalars().all()) == 1
        assert len(session.execute(select(OutboxEvent)).scalars().all()) == 1


def test_abandoned_processing_with_release_evidence_is_reconciled_as_replay():
    engine = _factory()
    now = datetime.now(timezone.utc)
    stale = now - timedelta(minutes=10)
    with Session(engine) as session:
        session.add_all([
            ReleaseAccount(account_id="REC2-SRC", balance=0, updated_at=now),
            ReleaseAccount(account_id="REC2-DST", balance=1000, updated_at=now),
            ReleaseEscrow(escrow_id="REC2-ESC", state="RELEASED", amount=1000, updated_at=stale),
            ReleaseOperation(
                idempotency_key="REC2-KEY",
                fingerprint="PLACEHOLDER",
                transaction_id="REC2-TX",
                escrow_id="REC2-ESC",
                destination="REC2-DST",
                amount=1000,
                state="PROCESSING",
                created_at=stale,
                updated_at=stale,
            ),
            ReleaseWitness(transaction_id="REC2-TX", event_type="RELEASED", amount=1000, created_at=stale),
            OutboxEvent(
                event_id="release:REC2-TX",
                event_type="GERCHAIN_RELEASED",
                aggregate_id="REC2-TX",
                payload_json="{}",
                state="PENDING",
                lease_until=None,
                attempts=0,
                created_at=stale,
                updated_at=stale,
            ),
        ])
        session.commit()
        payload = {"transaction_id": "REC2-TX", "escrow_id": "REC2-ESC", "source": "REC2-SRC", "destination": "REC2-DST", "amount": 1000}
        session.execute(
            ReleaseOperation.__table__.update()
            .where(ReleaseOperation.idempotency_key == "REC2-KEY")
            .values(fingerprint=IdempotencyEngine.fingerprint(payload))
        )
        session.commit()

    release = PostgreSQLAtomicRelease(lambda: Session(engine), processing_lease_seconds=60)
    result = release.release(
        idempotency_key="REC2-KEY",
        transaction_id="REC2-TX",
        escrow_id="REC2-ESC",
        source="REC2-SRC",
        destination="REC2-DST",
        amount=1000,
        decision_status="APPROVE",
        authorization_status="AUTHORIZED",
        trinity_proof=_proof(),
        evidence_verified=True,
    )

    assert result.replay is True
    with Session(engine) as session:
        op = session.execute(select(ReleaseOperation).where(ReleaseOperation.idempotency_key == "REC2-KEY")).scalar_one()
        assert op.state == "COMPLETED"
        assert len(session.execute(select(ReleaseWitness)).scalars().all()) == 1
        assert len(session.execute(select(OutboxEvent)).scalars().all()) == 1

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from persistence.atomic_release import ReleaseAccount, ReleaseEscrow, ReleaseOperation, ReleaseWitness, PostgreSQLAtomicRelease, initialize_atomic_release_schema
from persistence.recovery_outbox import OutboxEvent


def _factory():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    engine = create_engine(url, pool_pre_ping=True)
    initialize_atomic_release_schema(engine)
    return engine


def test_governance_rejection_is_pre_mutation(_factory= _factory):
    engine = _factory()
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        session.add_all([
            ReleaseAccount(account_id="FAIL-SRC", balance=1000, updated_at=now),
            ReleaseAccount(account_id="FAIL-DST", balance=0, updated_at=now),
            ReleaseEscrow(escrow_id="FAIL-ESC", state="LOCKED", amount=1000, updated_at=now),
        ])
        session.commit()

    release = PostgreSQLAtomicRelease(lambda: Session(engine))
    with pytest.raises(PermissionError):
        release.release(
            idempotency_key="FAIL-KEY", transaction_id="FAIL-TX", escrow_id="FAIL-ESC",
            source="FAIL-SRC", destination="FAIL-DST", amount=1000,
            decision_status="DENY", authorization_status="AUTHORIZED",
            trinity_proof={"trust": True, "transparency": True, "performance": True},
            evidence_verified=True,
        )

    with Session(engine) as session:
        assert session.get(ReleaseAccount, "FAIL-SRC").balance == 1000
        assert session.get(ReleaseAccount, "FAIL-DST").balance == 0
        assert session.get(ReleaseEscrow, "FAIL-ESC").state == "LOCKED"
        assert session.execute(select(ReleaseOperation)).scalars().all() == []
        assert session.execute(select(ReleaseWitness)).scalars().all() == []
        assert session.execute(select(OutboxEvent)).scalars().all() == []


def test_post_commit_response_loss_replays_completed_operation():
    engine = _factory()
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        session.add_all([
            ReleaseAccount(account_id="REPLAY-SRC", balance=1000, updated_at=now),
            ReleaseAccount(account_id="REPLAY-DST", balance=0, updated_at=now),
            ReleaseEscrow(escrow_id="REPLAY-ESC", state="LOCKED", amount=1000, updated_at=now),
        ])
        session.commit()

    release = PostgreSQLAtomicRelease(lambda: Session(engine))
    kwargs = dict(
        idempotency_key="REPLAY-KEY", transaction_id="REPLAY-TX", escrow_id="REPLAY-ESC",
        source="REPLAY-SRC", destination="REPLAY-DST", amount=1000,
        decision_status="APPROVE", authorization_status="AUTHORIZED",
        trinity_proof={"trust": True, "transparency": True, "performance": True},
        evidence_verified=True,
    )
    first = release.release(**kwargs)
    second = release.release(**kwargs)

    assert first.replay is False
    assert second.replay is True
    with Session(engine) as session:
        assert session.get(ReleaseAccount, "REPLAY-SRC").balance == 0
        assert session.get(ReleaseAccount, "REPLAY-DST").balance == 1000
        assert session.get(ReleaseEscrow, "REPLAY-ESC").state == "RELEASED"
        assert len(session.execute(select(ReleaseOperation)).scalars().all()) == 1
        assert len(session.execute(select(ReleaseWitness)).scalars().all()) == 1
        assert len(session.execute(select(OutboxEvent)).scalars().all()) == 1

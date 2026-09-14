from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from persistence.atomic_release import (
    PostgreSQLAtomicRelease,
    ReleaseAccount,
    ReleaseEscrow,
    ReleaseOperation,
    ReleaseWitness,
    initialize_atomic_release_schema,
)
from persistence.recovery_outbox import OutboxEvent


def test_completed_release_is_safe_after_response_loss():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    engine = create_engine(url, pool_pre_ping=True)
    initialize_atomic_release_schema(engine)
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        session.add_all([
            ReleaseAccount(account_id="LOSS-SRC", balance=2000, updated_at=now),
            ReleaseAccount(account_id="LOSS-DST", balance=0, updated_at=now),
            ReleaseEscrow(escrow_id="LOSS-ESC", state="LOCKED", amount=2000, updated_at=now),
        ])
        session.commit()

    release = PostgreSQLAtomicRelease(lambda: Session(engine))
    request = dict(
        idempotency_key="LOSS-KEY", transaction_id="LOSS-TX", escrow_id="LOSS-ESC",
        source="LOSS-SRC", destination="LOSS-DST", amount=2000,
        decision_status="APPROVE", authorization_status="AUTHORIZED",
        trinity_proof={"trust": True, "transparency": True, "performance": True},
        evidence_verified=True,
    )

    first = release.release(**request)
    assert first.replay is False

    # Simulate a client that did not receive the successful response and retries.
    replay = release.release(**request)
    assert replay.replay is True

    with Session(engine) as session:
        assert session.get(ReleaseAccount, "LOSS-SRC").balance == 0
        assert session.get(ReleaseAccount, "LOSS-DST").balance == 2000
        assert session.get(ReleaseEscrow, "LOSS-ESC").state == "RELEASED"
        assert len(session.execute(select(ReleaseOperation)).scalars().all()) == 1
        assert len(session.execute(select(ReleaseWitness)).scalars().all()) == 1
        assert len(session.execute(select(OutboxEvent)).scalars().all()) == 1

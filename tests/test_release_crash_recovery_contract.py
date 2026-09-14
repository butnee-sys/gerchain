from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from persistence.atomic_release import ReleaseAccount, ReleaseEscrow, ReleaseOperation, ReleaseWitness, PostgreSQLAtomicRelease, initialize_atomic_release_schema
from persistence.recovery_outbox import OutboxEvent, PostgreSQLOutbox


def governance_kwargs():
    return dict(decision_status="APPROVE", authorization_status="AUTHORIZED", trinity_proof={"trust": True, "transparency": True, "performance": True}, evidence_verified=True)


@pytest.fixture()
def db():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required")
    engine = create_engine(url, pool_pre_ping=True)
    initialize_atomic_release_schema(engine)
    now = datetime.now(timezone.utc)
    with Session(engine) as s:
        s.add_all([ReleaseAccount(account_id="CR-SRC", balance=5000, updated_at=now), ReleaseAccount(account_id="CR-DST", balance=0, updated_at=now), ReleaseEscrow(escrow_id="CR-ESC", state="LOCKED", amount=5000, updated_at=now)])
        s.commit()
    return engine


def test_release_is_replayable_after_post_commit_response_loss(db):
    service = PostgreSQLAtomicRelease(lambda: Session(db))
    first = service.release(idempotency_key="CR-KEY", transaction_id="CR-TX", escrow_id="CR-ESC", source="CR-SRC", destination="CR-DST", amount=5000, **governance_kwargs())
    assert first.replay is False

    retry = service.release(idempotency_key="CR-KEY", transaction_id="CR-TX", escrow_id="CR-ESC", source="CR-SRC", destination="CR-DST", amount=5000, **governance_kwargs())
    assert retry.replay is True

    with Session(db) as s:
        assert s.get(ReleaseAccount, "CR-SRC").balance == 0
        assert s.get(ReleaseAccount, "CR-DST").balance == 5000
        assert len(s.execute(select(ReleaseOperation)).scalars().all()) == 1
        assert len(s.execute(select(ReleaseWitness)).scalars().all()) == 1
        assert len(s.execute(select(OutboxEvent)).scalars().all()) == 1


def test_expired_outbox_processing_returns_to_pending(db):
    outbox = PostgreSQLOutbox(lambda: Session(db), lease_seconds=1)
    outbox.enqueue(event_id="CR-EVENT", event_type="GERCHAIN_RELEASED", aggregate_id="CR-TX", payload_json="{}")
    claimed = outbox.claim(limit=1)
    assert len(claimed) == 1

    with Session(db) as s:
        row = s.execute(select(OutboxEvent).where(OutboxEvent.event_id == "CR-EVENT")).scalar_one()
        row.lease_until = datetime.now(timezone.utc) - timedelta(seconds=1)
        s.commit()

    assert outbox.recover_expired(limit=10) == 1
    with Session(db) as s:
        row = s.execute(select(OutboxEvent).where(OutboxEvent.event_id == "CR-EVENT")).scalar_one()
        assert row.state == "PENDING"
        assert row.lease_until is None

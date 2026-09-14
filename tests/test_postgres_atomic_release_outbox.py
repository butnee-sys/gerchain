import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from persistence.atomic_release import ReleaseAccount, ReleaseEscrow, PostgreSQLAtomicRelease, initialize_atomic_release_schema
from persistence.recovery_outbox import OutboxEvent


@pytest.fixture()
def release_service():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    engine = create_engine(url, pool_pre_ping=True)
    initialize_atomic_release_schema(engine)
    now_service = PostgreSQLAtomicRelease(lambda: Session(engine))
    return now_service, engine


def governance():
    return dict(decision_status="APPROVE", authorization_status="AUTHORIZED", trinity_proof={"trust": True, "transparency": True, "performance": True}, evidence_verified=True)


def test_release_and_outbox_commit_together(release_service):
    service, engine = release_service
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    with Session(engine) as session:
        session.add_all([
            ReleaseAccount(account_id="SRC-OUTBOX", balance=2_000_000, updated_at=now),
            ReleaseAccount(account_id="DST-OUTBOX", balance=0, updated_at=now),
            ReleaseEscrow(escrow_id="ESC-OUTBOX", state="LOCKED", amount=2_000_000, updated_at=now),
        ])
        session.commit()

    result = service.release(idempotency_key="OUTBOX-RELEASE-1", transaction_id="TX-OUTBOX-1", escrow_id="ESC-OUTBOX", source="SRC-OUTBOX", destination="DST-OUTBOX", amount=2_000_000, **governance())
    assert result.replay is False

    with Session(engine) as session:
        src = session.get(ReleaseAccount, "SRC-OUTBOX")
        dst = session.get(ReleaseAccount, "DST-OUTBOX")
        escrow = session.get(ReleaseEscrow, "ESC-OUTBOX")
        event = session.execute(select(OutboxEvent).where(OutboxEvent.event_id == "release:TX-OUTBOX-1")).scalar_one()
        assert src.balance == 0
        assert dst.balance == 2_000_000
        assert escrow.state == "RELEASED"
        assert event.state == "PENDING"


def test_release_rollback_does_not_publish_outbox(release_service):
    service, engine = release_service
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    with Session(engine) as session:
        session.add_all([
            ReleaseAccount(account_id="SRC-ROLLBACK", balance=1, updated_at=now),
            ReleaseAccount(account_id="DST-ROLLBACK", balance=0, updated_at=now),
            ReleaseEscrow(escrow_id="ESC-ROLLBACK", state="LOCKED", amount=2, updated_at=now),
        ])
        session.commit()

    with pytest.raises(ValueError):
        service.release(idempotency_key="ROLLBACK-1", transaction_id="TX-ROLLBACK-1", escrow_id="ESC-ROLLBACK", source="SRC-ROLLBACK", destination="DST-ROLLBACK", amount=2, **governance())

    with Session(engine) as session:
        assert session.execute(select(OutboxEvent).where(OutboxEvent.event_id == "release:TX-ROLLBACK-1")).scalar_one_or_none() is None


def test_release_fails_closed_without_dee_authorization(release_service):
    service, engine = release_service
    with pytest.raises(PermissionError):
        service.release(idempotency_key="DENY-1", transaction_id="TX-DENY-1", escrow_id="ESC-MISSING", source="SRC", destination="DST", amount=1, decision_status="APPROVE", authorization_status="DENIED", trinity_proof={"trust": True, "transparency": True, "performance": True}, evidence_verified=True)


def test_release_fails_closed_when_g3_trinity_is_not_passed(release_service):
    service, engine = release_service
    with pytest.raises(PermissionError):
        service.release(idempotency_key="DENY-2", transaction_id="TX-DENY-2", escrow_id="ESC-MISSING", source="SRC", destination="DST", amount=1, decision_status="APPROVE", authorization_status="AUTHORIZED", trinity_proof={"trust": True, "transparency": False, "performance": True}, evidence_verified=True)

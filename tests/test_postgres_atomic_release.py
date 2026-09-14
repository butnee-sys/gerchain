import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from persistence.atomic_release import PostgreSQLAtomicRelease, ReleaseAccount, ReleaseEscrow, initialize_atomic_release_schema
from core.idempotency import IdempotencyConflictError


@pytest.fixture()
def release_service():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    engine = create_engine(url, pool_pre_ping=True)
    initialize_atomic_release_schema(engine)
    now_service = PostgreSQLAtomicRelease(lambda: Session(engine))
    from datetime import datetime, timezone
    with Session(engine) as session:
        now = datetime.now(timezone.utc)
        session.merge(ReleaseAccount(account_id="SRC", balance=10_000_000, updated_at=now))
        session.merge(ReleaseAccount(account_id="DST", balance=0, updated_at=now))
        session.merge(ReleaseEscrow(escrow_id="ESC-001", state="LOCKED", amount=2_000_000, updated_at=now))
        session.commit()
    return now_service


def test_release_is_atomic_and_replayable(release_service):
    first = release_service.release(idempotency_key="REL-001", transaction_id="TX-001", escrow_id="ESC-001", source="SRC", destination="DST", amount=2_000_000)
    replay = release_service.release(idempotency_key="REL-001", transaction_id="TX-001", escrow_id="ESC-001", source="SRC", destination="DST", amount=2_000_000)
    assert first.replay is False
    assert replay.replay is True


def test_release_key_conflict_is_denied(release_service):
    release_service.release(idempotency_key="REL-002", transaction_id="TX-002", escrow_id="ESC-001", source="SRC", destination="DST", amount=2_000_000)
    with pytest.raises(IdempotencyConflictError):
        release_service.release(idempotency_key="REL-002", transaction_id="TX-002", escrow_id="ESC-001", source="SRC", destination="OTHER", amount=2_000_000)

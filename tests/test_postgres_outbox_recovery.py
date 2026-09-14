import os
import time

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from persistence.recovery_outbox import OutboxEvent, PostgreSQLOutbox, initialize_outbox_schema


@pytest.fixture()
def outbox():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    engine = create_engine(url, pool_pre_ping=True)
    initialize_outbox_schema(engine)
    return PostgreSQLOutbox(lambda: Session(engine), lease_seconds=1), engine


def test_processing_event_returns_to_pending_after_lease_expiry(outbox):
    service, engine = outbox
    service.enqueue(event_id="OUTBOX-001", event_type="RELEASED", aggregate_id="TX-001", payload_json='{"amount":2000000}')
    claimed = service.claim()
    assert len(claimed) == 1
    time.sleep(1.1)
    assert service.recover_expired() == 1
    claimed_again = service.claim()
    assert len(claimed_again) == 1
    assert claimed_again[0].event_id == "OUTBOX-001"


def test_completed_event_is_not_recovered(outbox):
    service, engine = outbox
    service.enqueue(event_id="OUTBOX-002", event_type="RELEASED", aggregate_id="TX-002", payload_json='{}')
    assert len(service.claim()) == 1
    assert service.complete("OUTBOX-002") is True
    assert service.recover_expired() == 0

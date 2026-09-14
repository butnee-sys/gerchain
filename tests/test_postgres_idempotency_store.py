import os

import pytest

from core.idempotency import IdempotencyConflictError
from persistence.idempotency_store import build_postgres_session_factory, PostgreSQLIdempotencyStore


@pytest.fixture()
def store():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    return PostgreSQLIdempotencyStore(build_postgres_session_factory(url))


def test_same_key_same_payload_replays(store):
    payload = {"transaction_id": "TX-PG-001", "destination": "BENEFICIARY", "amount": 2_000_000}
    assert store.begin("release", "release:TX-PG-001", payload) is None
    store.complete("release", "release:TX-PG-001", payload, {"state": "RELEASED", "moved": 2_000_000})
    replay = store.begin("release", "release:TX-PG-001", payload)
    assert replay is not None
    assert replay.result["moved"] == 2_000_000


def test_same_key_different_payload_is_denied(store):
    first = {"transaction_id": "TX-PG-002", "destination": "BENEFICIARY", "amount": 2_000_000}
    second = {"transaction_id": "TX-PG-002", "destination": "OTHER", "amount": 2_000_000}
    store.begin("release", "release:TX-PG-002", first)
    with pytest.raises(IdempotencyConflictError):
        store.begin("release", "release:TX-PG-002", second)

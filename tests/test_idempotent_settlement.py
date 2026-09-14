import pytest

from core.idempotency import IdempotencyConflictError, IdempotencyEngine


def test_duplicate_release_returns_original_result():
    guard = IdempotencyEngine()
    payload = {
        "operation": "release",
        "transaction_id": "TX-001",
        "destination": "PERSON-001",
    }

    first = {"state": "RELEASED", "amount": 2_000_000}
    assert guard.complete("release:TX-001", payload, first) == first
    assert guard.begin("release:TX-001", payload) == first


def test_reusing_release_key_for_different_destination_is_denied():
    guard = IdempotencyEngine()
    first_payload = {
        "operation": "release",
        "transaction_id": "TX-002",
        "destination": "PERSON-001",
    }
    second_payload = {
        "operation": "release",
        "transaction_id": "TX-002",
        "destination": "PERSON-002",
    }

    guard.complete("release:TX-002", first_payload, {"state": "RELEASED"})

    with pytest.raises(IdempotencyConflictError):
        guard.begin("release:TX-002", second_payload)

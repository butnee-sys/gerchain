import pytest

from core.idempotency import IdempotencyConflictError, IdempotencyEngine


def test_same_key_same_request_returns_original_result():
    engine = IdempotencyEngine()
    payload = {"transaction_id": "TX-1", "amount": 100}

    assert engine.begin("KEY-1", payload) is None
    first = engine.complete("KEY-1", payload, {"status": "COMPLETED", "movement": 100})
    second = engine.begin("KEY-1", payload)

    assert second == first


def test_same_key_different_request_fails_closed():
    engine = IdempotencyEngine()
    engine.complete("KEY-1", {"transaction_id": "TX-1", "amount": 100}, "DONE")

    with pytest.raises(IdempotencyConflictError):
        engine.begin("KEY-1", {"transaction_id": "TX-1", "amount": 200})


def test_missing_key_is_rejected():
    engine = IdempotencyEngine()

    with pytest.raises(ValueError):
        engine.begin("", {"transaction_id": "TX-1"})

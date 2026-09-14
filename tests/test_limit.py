import pytest

from core.limit import LimitEngine, LimitExceededError, LimitRule


def test_single_transaction_limit():
    engine = LimitEngine()
    engine.add(
        LimitRule(
            limit_id="L-001",
            subject_id="INSURER-001",
            currency="MNT",
            max_amount=2_000_000,
        )
    )

    engine.check(limit_id="L-001", amount=2_000_000)


def test_limit_rejects_excess_amount():
    engine = LimitEngine()
    engine.add(
        LimitRule(
            limit_id="L-002",
            subject_id="INSURER-001",
            currency="MNT",
            max_amount=2_000_000,
        )
    )

    with pytest.raises(LimitExceededError):
        engine.check(limit_id="L-002", amount=2_000_001)


def test_cumulative_limit_uses_current_exposure():
    engine = LimitEngine()
    engine.add(
        LimitRule(
            limit_id="L-003",
            subject_id="INSURER-001",
            currency="MNT",
            max_amount=2_000_000,
            cumulative=True,
        )
    )

    with pytest.raises(LimitExceededError):
        engine.check(limit_id="L-003", amount=500_001, current_amount=1_500_000)

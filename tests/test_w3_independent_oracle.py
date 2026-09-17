from tests.oracles.w3_independent_oracle import (
    evaluate_concurrent_upgrades,
    stale_predecessor_is_safe,
)


def test_distinct_concurrent_upgrades_have_one_authoritative_successor():
    result = evaluate_concurrent_upgrades(
        current_version=1,
        upgrades=(
            ("u1", 1, 2),
            ("u2", 1, 2),
        ),
    )

    assert result.accepted_upgrade_ids == ("u1",)
    assert result.final_version == 2
    assert result.split_brain is False


def test_same_upgrade_retry_is_idempotent():
    result = evaluate_concurrent_upgrades(
        current_version=1,
        upgrades=(
            ("u1", 1, 2),
            ("u1", 1, 2),
        ),
    )

    assert result.accepted_upgrade_ids == ("u1",)
    assert result.final_version == 2
    assert result.idempotent_retry_safe is True


def test_stale_predecessor_is_not_safe():
    assert stale_predecessor_is_safe(current_version=2, from_version=1) is False
    assert stale_predecessor_is_safe(current_version=1, from_version=1) is True

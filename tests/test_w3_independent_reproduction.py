"""Deterministic W3 semantic reproduction outside persistence."""

from tests.oracles.w3_independent_oracle import evaluate_concurrent_upgrades


def test_w3_reproduction_is_deterministic():
    scenario = (
        ("upgrade-A", 7, 8),
        ("upgrade-B", 7, 8),
        ("upgrade-A", 7, 8),
    )
    expected = ("upgrade-A",)

    first = evaluate_concurrent_upgrades(current_version=7, upgrades=scenario)
    second = evaluate_concurrent_upgrades(current_version=7, upgrades=scenario)

    assert first == second
    assert first.accepted_upgrade_ids == expected
    assert first.final_version == 8
    assert first.split_brain is False
    assert first.idempotent_retry_safe is True

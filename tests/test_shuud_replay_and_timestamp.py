"""Adversarial SHUUD tests for replay and temporal integrity."""

from copy import deepcopy

from shuud.independent_verifier import SHUUDIndependentVerifier

from tests.test_shuud_witness_tamper import _bundle


def test_verifier_rejects_replayed_witness_entry():
    bundle = _bundle()
    replayed = deepcopy(bundle["entries"][1])
    bundle["entries"].insert(2, replayed)

    result = SHUUDIndependentVerifier().verify_bundle(bundle)

    assert result.verified is False
    assert "GERCHAIN_BUNDLE_INVALID" in result.reasons


def test_verifier_rejects_timestamp_regression():
    bundle = _bundle(
        timestamps=(
            "2026-09-12T00:00:10+00:00",
            "2026-09-12T00:00:15+00:00",
            "2026-09-12T00:00:20+00:00",
            "2026-09-12T00:00:25+00:00",
            "2026-09-11T23:59:59+00:00",
            "2026-09-12T00:01:00+00:00",
        )
    )

    result = SHUUDIndependentVerifier().verify_bundle(bundle)

    assert result.verified is False
    assert "TIMESTAMP_ORDER_INVALID" in result.reasons


def test_verifier_uses_sequence_not_timestamp_for_lifecycle_order():
    equal_timestamp = "2026-09-12T00:00:00+00:00"
    bundle = _bundle(timestamps=(equal_timestamp,) * 6)

    result = SHUUDIndependentVerifier().verify_bundle(bundle)

    assert result.verified is True

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
    bundle = _bundle()
    bundle["entries"][4]["record"]["timestamp"] = "2026-09-11T23:59:59+00:00"

    result = SHUUDIndependentVerifier().verify_bundle(bundle)

    assert result.verified is False
    assert "TIMESTAMP_ORDER_INVALID" in result.reasons


def test_verifier_uses_sequence_not_timestamp_for_lifecycle_order():
    bundle = _bundle()
    # Keep the authoritative event sequence intact while making timestamps
    # equal. Equal timestamps must not reorder a valid sequence.
    for entry in bundle["entries"]:
        entry["record"]["timestamp"] = "2026-09-12T00:00:00+00:00"

    result = SHUUDIndependentVerifier().verify_bundle(bundle)

    assert result.verified is True

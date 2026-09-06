import json
from dataclasses import replace

import pytest

from persistence.serializer import serialize_chain
from verifier.independent_verifier import IndependentVerifier
from witness.chain import WitnessChain


@pytest.fixture
def witness_chains():
    initial_state = {
        "initialized": False,
        "sequence_counter": 0,
    }

    manifest = {
        "project": "V79.2-Independent-Multi-Witness",
        "version": "1",
    }

    return [
        WitnessChain(
            initial_state=initial_state,
            manifest=manifest,
            witness_id=f"witness-{i}",
        )
        for i in range(1, 4)
    ]


def create_event(chain):
    return chain.append_event(
        event_id="EVENT-001",
        event_type="TEST_EVENT",
        timestamp="2026-09-03T13:20:00Z",
        payload={
            "value": 100,
            "action": "test",
        },
        evidence={
            "document": "evidence-001",
        },
    )


def test_independent_verifier_accepts_serialized_bundle(
    witness_chains,
):
    create_event(witness_chains[0])

    bundle_bytes = serialize_chain(
        witness_chains[0]
    )

    verifier = IndependentVerifier()

    assert verifier.verify_bytes(bundle_bytes) is True


def test_tampered_serialized_event_is_rejected(
    witness_chains,
):
    create_event(witness_chains[0])

    bundle = json.loads(
        serialize_chain(
            witness_chains[0]
        ).decode("utf-8")
    )

    bundle["entries"][0]["event_payload"]["value"] = 999

    tampered_bytes = json.dumps(
        bundle,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    verifier = IndependentVerifier()

    assert verifier.verify_bytes(
        tampered_bytes
    ) is False


def test_tampered_serialized_evidence_is_rejected(
    witness_chains,
):
    create_event(witness_chains[0])

    bundle = json.loads(
        serialize_chain(
            witness_chains[0]
        ).decode("utf-8")
    )

    bundle["entries"][0]["evidence"]["document"] = (
        "tampered-evidence"
    )

    tampered_bytes = json.dumps(
        bundle,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    verifier = IndependentVerifier()

    assert verifier.verify_bytes(
        tampered_bytes
    ) is False


def test_tampered_serialized_manifest_is_rejected(
    witness_chains,
):
    create_event(witness_chains[0])

    bundle = json.loads(
        serialize_chain(
            witness_chains[0]
        ).decode("utf-8")
    )

    bundle["manifest"]["version"] = "999"

    tampered_bytes = json.dumps(
        bundle,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    verifier = IndependentVerifier()

    assert verifier.verify_bytes(
        tampered_bytes
    ) is False


def test_three_independent_serialized_witnesses_verify(
    witness_chains,
):
    for chain in witness_chains:
        create_event(chain)

    verifier = IndependentVerifier()

    bundles = [
        serialize_chain(chain)
        for chain in witness_chains
    ]

    results = [
        verifier.verify_bytes(bundle)
        for bundle in bundles
    ]

    assert results == [
        True,
        True,
        True,
    ]


def test_one_tampered_witness_can_be_rejected_without_invalidating_two_valid_witnesses(
    witness_chains,
):
    for chain in witness_chains:
        create_event(chain)

    bundles = [
        serialize_chain(chain)
        for chain in witness_chains
    ]

    tampered_bundle = json.loads(
        bundles[2].decode("utf-8")
    )

    tampered_bundle["entries"][0]["event_payload"][
        "value"
    ] = 777

    bundles[2] = json.dumps(
        tampered_bundle,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    verifier = IndependentVerifier()

    valid_results = [
        verifier.verify_bytes(bundle)
        for bundle in bundles
    ]

    assert valid_results == [
        True,
        True,
        False,
    ]

    assert sum(valid_results) == 2
import json
import pytest

from persistence.serializer import serialize_chain
from witness.chain import WitnessChain
from witness.independent_multi import (
    IndependentMultiWitnessEngine,
)


def create_witness_chains():
    initial_state = {
        "initialized": False,
        "sequence_counter": 0,
    }

    manifest = {
        "project": "V79.2.1-Authorized-Witness-Set",
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


def test_authorized_witnesses_reach_consensus():
    chains = create_witness_chains()

    for chain in chains:
        create_event(chain)

    bundles = [
        serialize_chain(chain)
        for chain in chains
    ]

    engine = IndependentMultiWitnessEngine(
        quorum=2,
        authorized_witness_ids={
            "witness-1",
            "witness-2",
            "witness-3",
        },
    )

    result = engine.evaluate(bundles)

    assert result.status == "CONSENSUS"
    assert result.votes == 3
    assert result.quorum == 2
    assert result.consensus_hash is not None


def test_unknown_witness_cannot_count_toward_quorum():
    chains = create_witness_chains()

    for chain in chains:
        create_event(chain)

    unknown = WitnessChain(
        initial_state=chains[0].initial_state,
        manifest=chains[0].manifest,
        witness_id="attacker",
    )

    create_event(unknown)

    bundles = [
        serialize_chain(chains[0]),
        serialize_chain(unknown),
    ]

    engine = IndependentMultiWitnessEngine(
        quorum=2,
        authorized_witness_ids={
            "witness-1",
            "witness-2",
            "witness-3",
        },
    )

    result = engine.evaluate(bundles)

    assert result.status == "REJECTED"
    assert result.votes == 1
    assert "attacker" in result.invalid_witness_ids


def test_authorized_quorum_cannot_be_fabricated_by_duplicate_bundle():
    chains = create_witness_chains()

    for chain in chains:
        create_event(chain)

    bundles = [
        serialize_chain(chains[0]),
        serialize_chain(chains[0]),
        serialize_chain(chains[0]),
    ]

    engine = IndependentMultiWitnessEngine(
        quorum=2,
        authorized_witness_ids={
            "witness-1",
            "witness-2",
            "witness-3",
        },
    )

    result = engine.evaluate(bundles)

    assert result.status == "REJECTED"
    assert result.votes == 1
    assert result.valid_witness_ids == [
        "witness-1",
    ]


def test_authorized_witness_set_rejects_missing_quorum():
    chains = create_witness_chains()

    for chain in chains:
        create_event(chain)

    bundles = [
        serialize_chain(chains[0]),
    ]

    engine = IndependentMultiWitnessEngine(
        quorum=2,
        authorized_witness_ids={
            "witness-1",
            "witness-2",
            "witness-3",
        },
    )

    result = engine.evaluate(bundles)

    assert result.status == "REJECTED"
    assert result.votes == 1
    assert result.quorum == 2


def test_tampered_authorized_witness_is_rejected():
    chains = create_witness_chains()

    for chain in chains:
        create_event(chain)

    bundles = [
        serialize_chain(chain)
        for chain in chains
    ]

    tampered = json.loads(
        bundles[0].decode("utf-8")
    )

    tampered["entries"][0]["event_payload"][
        "value"
    ] = 999

    bundles[0] = json.dumps(
        tampered,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    engine = IndependentMultiWitnessEngine(
        quorum=2,
        authorized_witness_ids={
            "witness-1",
            "witness-2",
            "witness-3",
        },
    )

    result = engine.evaluate(bundles)

    assert result.status == "CONSENSUS"
    assert result.votes == 2
    assert result.valid_witness_ids == [
        "witness-2",
        "witness-3",
    ]
    assert result.invalid_witness_ids == [
        "witness-1",
    ]


def test_authorized_set_must_not_be_smaller_than_quorum():
    with pytest.raises(
        ValueError,
        match="Authorized witness count cannot be smaller than quorum",
    ):
        IndependentMultiWitnessEngine(
            quorum=3,
            authorized_witness_ids={
                "witness-1",
                "witness-2",
            },
        )
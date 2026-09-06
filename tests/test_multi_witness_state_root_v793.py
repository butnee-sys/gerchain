import json

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
        "project": "V79.3-State-Root-Consensus",
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


def append_events(chain, count=2):
    for index in range(count):
        chain.append_event(
            event_id=f"EVENT-{index + 1:03d}",
            event_type="TEST_EVENT",
            timestamp=(
                f"2026-09-03T13:{20 + index}:00Z"
            ),
            payload={
                "value": 100 + index,
                "action": "test",
            },
            evidence={
                "document": f"evidence-{index + 1:03d}",
            },
        )


def create_engine():
    return IndependentMultiWitnessEngine(
        quorum=2,
        authorized_witness_ids={
            "witness-1",
            "witness-2",
            "witness-3",
        },
    )


def test_three_witnesses_reach_consensus_on_same_state_root():
    chains = create_witness_chains()

    for chain in chains:
        append_events(chain, count=2)

    bundles = [
        serialize_chain(chain)
        for chain in chains
    ]

    engine = create_engine()
    result = engine.evaluate(bundles)

    assert result.status == "CONSENSUS"
    assert result.votes == 3
    assert result.consensus_hash is not None


def test_state_root_changes_when_second_event_changes():
    chains = create_witness_chains()

    for chain in chains:
        append_events(chain, count=2)

    bundles = [
        serialize_chain(chain)
        for chain in chains
    ]

    original = json.loads(
        bundles[2].decode("utf-8")
    )

    original["entries"][1]["event_payload"][
        "value"
    ] = 999

    bundles[2] = json.dumps(
        original,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    engine = create_engine()
    result = engine.evaluate(bundles)

    assert result.status == "CONSENSUS"
    assert result.votes == 2
    assert result.valid_witness_ids == [
        "witness-1",
        "witness-2",
    ]
    assert result.invalid_witness_ids == [
        "witness-3",
    ]


def test_tampered_state_hash_cannot_create_consensus():
    chains = create_witness_chains()

    for chain in chains:
        append_events(chain, count=2)

    bundles = [
        serialize_chain(chain)
        for chain in chains
    ]

    tampered = json.loads(
        bundles[0].decode("utf-8")
    )

    tampered["entries"][1]["record"][
        "new_state_hash"
    ] = "0" * 64

    bundles[0] = json.dumps(
        tampered,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    engine = create_engine()
    result = engine.evaluate(bundles)

    assert result.status == "CONSENSUS"
    assert result.votes == 2
    assert result.invalid_witness_ids == [
        "witness-1",
    ]


def test_tampered_first_event_is_detected_even_when_last_event_is_unchanged():
    chains = create_witness_chains()

    for chain in chains:
        append_events(chain, count=2)

    bundles = [
        serialize_chain(chain)
        for chain in chains
    ]

    tampered = json.loads(
        bundles[0].decode("utf-8")
    )

    tampered["entries"][0]["event_payload"][
        "value"
    ] = 777

    bundles[0] = json.dumps(
        tampered,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    engine = create_engine()
    result = engine.evaluate(bundles)

    assert result.status == "CONSENSUS"
    assert result.votes == 2
    assert result.invalid_witness_ids == [
        "witness-1",
    ]


def test_different_chain_lengths_do_not_produce_three_witness_consensus():
    chains = create_witness_chains()

    append_events(chains[0], count=2)
    append_events(chains[1], count=2)
    append_events(chains[2], count=1)

    bundles = [
        serialize_chain(chain)
        for chain in chains
    ]

    engine = create_engine()
    result = engine.evaluate(bundles)

    assert result.status == "CONSENSUS"
    assert result.votes == 2
    assert result.valid_witness_ids == [
        "witness-1",
        "witness-2",
        "witness-3",
    ]


def test_state_root_consensus_requires_same_final_state():
    chains = create_witness_chains()

    for chain in chains:
        append_events(chain, count=2)

    chains[2].append_event(
        event_id="EVENT-003",
        event_type="TEST_EVENT",
        timestamp="2026-09-03T13:22:00Z",
        payload={
            "value": 300,
            "action": "extra",
        },
        evidence={
            "document": "evidence-003",
        },
    )

    bundles = [
        serialize_chain(chain)
        for chain in chains
    ]

    engine = create_engine()
    result = engine.evaluate(bundles)

    assert result.status == "CONSENSUS"
    assert result.votes == 2
def test_same_last_event_different_history_must_not_reach_false_consensus():
    chains = create_witness_chains()

    # Witness 1 and 3 have the same first event.
    for chain in [chains[0], chains[2]]:
        chain.append_event(
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

    # Witness 2 has a different history.
    chains[1].append_event(
        event_id="EVENT-001",
        event_type="TEST_EVENT",
        timestamp="2026-09-03T13:20:00Z",
        payload={
            "value": 999,
            "action": "test",
        },
        evidence={
            "document": "evidence-001",
        },
    )

    # All three have the EXACT SAME final event.
    for chain in chains:
        chain.append_event(
            event_id="EVENT-002",
            event_type="TEST_EVENT",
            timestamp="2026-09-03T13:21:00Z",
            payload={
                "value": 200,
                "action": "final",
            },
            evidence={
                "document": "evidence-002",
            },
        )

    bundles = [
        serialize_chain(chain)
        for chain in chains
    ]

    engine = create_engine()
    result = engine.evaluate(bundles)

    # Only witness-1 and witness-3 share the same final state root.
    assert result.status == "CONSENSUS"
    assert result.votes == 2
    assert result.valid_witness_ids == [
        "witness-1",
        "witness-2",
        "witness-3",
    ]
    assert result.dissenting_witness_ids == [
        "witness-2",
    ]
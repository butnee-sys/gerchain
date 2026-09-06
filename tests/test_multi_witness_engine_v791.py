import pytest
from dataclasses import replace

from core.hashing import domain_hash
from witness.chain import WitnessChain


@pytest.fixture
def witness_chains():
    initial_state = {
        "initialized": False,
        "sequence_counter": 0,
    }

    manifest = {
        "project": "V79.1-Multi-Witness-Engine",
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


def test_two_of_three_reaches_consensus(witness_chains):
    from witness.multi import MultiWitnessEngine

    records = [
        create_event(witness_chains[0]),
        create_event(witness_chains[1]),
        create_event(witness_chains[2]),
    ]

    tampered_hash = domain_hash(
        "WITNESS_EVENT",
        {
            "sequence": 1,
            "event_id": "EVENT-001",
            "event_type": "TEST_EVENT",
            "timestamp": "2026-09-03T13:20:00Z",
            "payload": {
                "value": 999,
                "action": "tampered",
            },
        },
    )

    records[2] = replace(
        records[2],
        event_hash=tampered_hash,
    )

    engine = MultiWitnessEngine(
        witnesses=witness_chains,
        quorum=2,
    )

    result = engine.evaluate(records)

    assert result.status == "CONSENSUS"
    assert result.consensus_hash == records[0].event_hash
    assert result.votes == 2
    assert result.quorum == 2


def test_three_different_hashes_are_rejected(witness_chains):
    from witness.multi import MultiWitnessEngine

    records = [
        create_event(witness_chains[0]),
        create_event(witness_chains[1]),
        create_event(witness_chains[2]),
    ]

    for index, record in enumerate(records):
        different_hash = domain_hash(
            "WITNESS_EVENT",
            {
                "sequence": 1,
                "event_id": f"DIFFERENT-{index}",
                "event_type": "TEST_EVENT",
                "timestamp": "2026-09-03T13:20:00Z",
                "payload": {
                    "value": index + 1,
                },
            },
        )

        records[index] = replace(
            record,
            event_hash=different_hash,
        )

    engine = MultiWitnessEngine(
        witnesses=witness_chains,
        quorum=2,
    )

    result = engine.evaluate(records)

    assert result.status == "REJECTED"
    assert result.consensus_hash is None
    assert result.votes == 0
    assert result.quorum == 2
    assert result.dissenting_witness_ids == [
        "witness-1",
        "witness-2",
        "witness-3",
    ]


def test_consensus_identifies_dissenting_witness(witness_chains):
    from witness.multi import MultiWitnessEngine

    records = [
        create_event(witness_chains[0]),
        create_event(witness_chains[1]),
        create_event(witness_chains[2]),
    ]

    bad_hash = domain_hash(
        "WITNESS_EVENT",
        {
            "sequence": 1,
            "event_id": "BAD-EVENT",
            "event_type": "TEST_EVENT",
            "timestamp": "2026-09-03T13:20:00Z",
            "payload": {
                "value": 999,
            },
        },
    )

    records[2] = replace(
        records[2],
        event_hash=bad_hash,
    )

    engine = MultiWitnessEngine(
        witnesses=witness_chains,
        quorum=2,
    )

    result = engine.evaluate(records)

    assert result.status == "CONSENSUS"
    assert result.dissenting_witness_ids == ["witness-3"]


def test_all_three_agree(witness_chains):
    from witness.multi import MultiWitnessEngine

    records = [
        create_event(witness_chains[0]),
        create_event(witness_chains[1]),
        create_event(witness_chains[2]),
    ]

    engine = MultiWitnessEngine(
        witnesses=witness_chains,
        quorum=2,
    )

    result = engine.evaluate(records)

    assert result.status == "CONSENSUS"
    assert result.votes == 3
    assert result.consensus_hash == records[0].event_hash
    assert result.dissenting_witness_ids == []


def test_invalid_quorum_is_rejected(witness_chains):
    from witness.multi import MultiWitnessEngine

    with pytest.raises(ValueError):
        MultiWitnessEngine(
            witnesses=witness_chains,
            quorum=1,
        )


def test_duplicate_witness_ids_are_rejected():
    from witness.multi import MultiWitnessEngine

    initial_state = {
        "initialized": False,
        "sequence_counter": 0,
    }

    manifest = {
        "project": "V79.1",
        "version": "1",
    }

    witness_a = WitnessChain(
        initial_state=initial_state,
        manifest=manifest,
        witness_id="same-id",
    )

    witness_b = WitnessChain(
        initial_state=initial_state,
        manifest=manifest,
        witness_id="same-id",
    )

    with pytest.raises(ValueError):
        MultiWitnessEngine(
            witnesses=[witness_a, witness_b],
            quorum=2,
        )
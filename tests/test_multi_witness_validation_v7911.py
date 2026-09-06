import pytest
from dataclasses import replace

from witness.chain import WitnessChain


@pytest.fixture
def witness_chains():
    initial_state = {
        "initialized": False,
        "sequence_counter": 0,
    }

    manifest = {
        "project": "V79.1.1-Witness-Validation",
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


def test_all_valid_witness_records_are_accepted(witness_chains):
    from witness.multi import MultiWitnessEngine

    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    engine = MultiWitnessEngine(
        witnesses=witness_chains,
        quorum=2,
    )

    result = engine.evaluate(records)

    assert result.status == "CONSENSUS"
    assert result.votes == 3


def test_tampered_event_hash_is_rejected(witness_chains):
    from witness.multi import MultiWitnessEngine

    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    records[2] = replace(
        records[2],
        event_hash="0" * 64,
    )

    engine = MultiWitnessEngine(
        witnesses=witness_chains,
        quorum=2,
    )

    result = engine.evaluate(records)

    assert result.status == "CONSENSUS"
    assert result.votes == 2
    assert result.dissenting_witness_ids == [
        "witness-3"
    ]


def test_tampered_state_hash_is_detected(witness_chains):
    from witness.multi import MultiWitnessEngine

    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    records[1] = replace(
        records[1],
        new_state_hash="1" * 64,
    )

    engine = MultiWitnessEngine(
        witnesses=witness_chains,
        quorum=2,
    )

    result = engine.evaluate(records)

    assert result.status == "CONSENSUS"
    assert result.votes == 2
    assert result.dissenting_witness_ids == [
        "witness-2"
    ]


def test_tampered_previous_state_hash_is_detected(
    witness_chains,
):
    from witness.multi import MultiWitnessEngine

    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    records[0] = replace(
        records[0],
        previous_state_hash="2" * 64,
    )

    engine = MultiWitnessEngine(
        witnesses=witness_chains,
        quorum=2,
    )

    result = engine.evaluate(records)

    assert result.status == "CONSENSUS"
    assert result.votes == 2
    assert result.dissenting_witness_ids == [
        "witness-1"
    ]


def test_tampered_manifest_hash_is_detected(
    witness_chains,
):
    from witness.multi import MultiWitnessEngine

    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    records[1] = replace(
        records[1],
        manifest_hash="3" * 64,
    )

    engine = MultiWitnessEngine(
        witnesses=witness_chains,
        quorum=2,
    )

    result = engine.evaluate(records)

    assert result.status == "CONSENSUS"
    assert result.votes == 2
    assert result.dissenting_witness_ids == [
        "witness-2"
    ]


def test_tampered_evidence_hash_is_detected(
    witness_chains,
):
    from witness.multi import MultiWitnessEngine

    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    records[2] = replace(
        records[2],
        evidence_hash="4" * 64,
    )

    engine = MultiWitnessEngine(
        witnesses=witness_chains,
        quorum=2,
    )

    result = engine.evaluate(records)

    assert result.status == "CONSENSUS"
    assert result.votes == 2
    assert result.dissenting_witness_ids == [
        "witness-3"
    ]


def test_invalid_witness_id_is_detected(
    witness_chains,
):
    from witness.multi import MultiWitnessEngine

    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    records[0] = replace(
        records[0],
        witness_id="unknown-witness",
    )

    engine = MultiWitnessEngine(
        witnesses=witness_chains,
        quorum=2,
    )

    result = engine.evaluate(records)

    assert result.status == "CONSENSUS"
    assert result.votes == 2
    assert result.dissenting_witness_ids == [
        "unknown-witness"
    ]


def test_wrong_event_id_is_detected(
    witness_chains,
):
    from witness.multi import MultiWitnessEngine

    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    records[2] = replace(
        records[2],
        event_id="EVENT-TAMPERED",
    )

    engine = MultiWitnessEngine(
        witnesses=witness_chains,
        quorum=2,
    )

    result = engine.evaluate(records)

    assert result.status == "CONSENSUS"
    assert result.votes == 2
    assert result.dissenting_witness_ids == [
        "witness-3"
    ]
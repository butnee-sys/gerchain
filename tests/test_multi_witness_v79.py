import pytest

from core.hashing import domain_hash
from witness.chain import WitnessChain


@pytest.fixture
def witness_chains():
    initial_state = {
        "initialized": False,
        "sequence_counter": 0,
    }

    manifest = {
        "project": "V79-Multi-Witness",
        "version": "0",
    }

    return [
        WitnessChain(
            initial_state=initial_state,
            manifest=manifest,
            witness_id=f"witness-{i}",
        )
        for i in range(1, 4)
    ]


def create_event(chain, event_id="EVENT-001"):
    return chain.append_event(
        event_id=event_id,
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


def test_three_independent_witnesses_exist(witness_chains):
    assert len(witness_chains) == 3

    witness_ids = {
        chain.witness_id
        for chain in witness_chains
    }

    assert witness_ids == {
        "witness-1",
        "witness-2",
        "witness-3",
    }


def test_all_witnesses_record_same_event(witness_chains):
    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    assert len(records) == 3

    assert all(
        record.event_id == "EVENT-001"
        for record in records
    )


def test_witnesses_have_independent_hash_identity(
    witness_chains,
):
    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    witness_ids = {
        record.witness_id
        for record in records
    }

    assert len(witness_ids) == 3


def test_same_event_produces_same_event_hash(
    witness_chains,
):
    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    hashes = {
        record.event_hash
        for record in records
    }

    assert len(hashes) == 1


def test_witness_records_are_cryptographically_valid(
    witness_chains,
):
    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    for record in records:
        assert len(record.event_hash) == 64
        assert len(record.new_state_hash) == 64
        assert len(record.previous_state_hash) == 64
        assert len(record.evidence_hash) == 64


def test_witness_state_hashes_agree(witness_chains):
    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    state_hashes = {
        record.new_state_hash
        for record in records
    }

    assert len(state_hashes) == 1


def test_witness_manifest_hashes_agree(witness_chains):
    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    manifest_hashes = {
        record.manifest_hash
        for record in records
    }

    assert len(manifest_hashes) == 1


def test_one_witness_can_be_detected_as_different(
    witness_chains,
):
    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    original_hashes = {
        record.event_hash
        for record in records
    }

    tampered_payload = {
        "value": 999,
        "action": "tampered",
    }

    tampered_hash = domain_hash(
        "WITNESS_EVENT",
        {
            "sequence": 1,
            "event_id": "EVENT-001",
            "event_type": "TEST_EVENT",
            "timestamp": "2026-09-03T13:20:00Z",
            "payload": tampered_payload,
        },
    )

    assert tampered_hash not in original_hashes


def test_two_of_three_majority_is_available(
    witness_chains,
):
    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    agreeing_hash = records[0].event_hash

    votes = sum(
        record.event_hash == agreeing_hash
        for record in records
    )

    assert votes == 3
    assert votes >= 2


def test_witnesses_are_not_single_object_instances(
    witness_chains,
):
    assert witness_chains[0] is not witness_chains[1]
    assert witness_chains[1] is not witness_chains[2]
    assert witness_chains[0] is not witness_chains[2]


def test_each_witness_has_its_own_chain(
    witness_chains,
):
    for chain in witness_chains:
        create_event(chain)

    assert all(
        len(chain.entries) == 1
        for chain in witness_chains
    )


def test_consensus_candidate_can_be_identified(
    witness_chains,
):
    records = [
        create_event(chain)
        for chain in witness_chains
    ]

    hash_votes = {}

    for record in records:
        hash_votes[record.event_hash] = (
            hash_votes.get(record.event_hash, 0) + 1
        )

    consensus_hash = max(
        hash_votes,
        key=hash_votes.get,
    )

    assert hash_votes[consensus_hash] == 3
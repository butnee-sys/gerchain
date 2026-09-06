import pytest

from core.hashing import domain_hash
from escrow.engine import EscrowEngine
from witness.chain import WitnessChain


@pytest.fixture
def escrow():
    witness_chain = WitnessChain(
        initial_state={
            "initialized": False,
            "sequence_counter": 0,
        },
        manifest={
            "project": "V77-Escrow",
            "version": "0",
        },
        witness_id="witness-escrow-01",
    )

    return EscrowEngine(
        escrow_id="ESC-001",
        amount=1000000,
        currency="MNT",
        witness_chain=witness_chain,
    )


def test_initial_state(escrow):
    state = escrow.get_state()

    assert state["escrow_id"] == "ESC-001"
    assert state["state"] == "CREATED"
    assert state["amount"] == 1000000
    assert state["currency"] == "MNT"
    assert state["transition_counter"] == 0


def test_valid_lifecycle(escrow):
    escrow.transition(
        "FUNDED",
        "2026-09-03T00:00:00Z",
        {"doc": "funding-001"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T00:01:00Z",
        {"doc": "lock-001"},
    )

    escrow.transition(
        "RELEASED",
        "2026-09-03T00:02:00Z",
        {"doc": "release-001"},
    )

    state = escrow.get_state()

    assert state["state"] == "RELEASED"
    assert state["transition_counter"] == 3


def test_refund_path(escrow):
    escrow.transition(
        "FUNDED",
        "2026-09-03T01:00:00Z",
        {"doc": "funding-002"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T01:00:30Z",
        {"doc": "lock-002"},
    )

    escrow.transition(
        "REFUNDED",
        "2026-09-03T01:01:00Z",
        {"doc": "refund-002"},
    )

    state = escrow.get_state()

    assert state["state"] == "REFUNDED"
    assert state["transition_counter"] == 3


def test_invalid_transition_created_to_released(escrow):
    with pytest.raises(ValueError):
        escrow.transition(
            "RELEASED",
            "2026-09-03T02:00:00Z",
            {"doc": "invalid-001"},
        )


def test_invalid_transition_released_to_refunded(escrow):
    escrow.transition(
        "FUNDED",
        "2026-09-03T03:00:00Z",
        {"doc": "funding-003"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T03:01:00Z",
        {"doc": "lock-003"},
    )

    escrow.transition(
        "RELEASED",
        "2026-09-03T03:02:00Z",
        {"doc": "release-003"},
    )

    with pytest.raises(ValueError):
        escrow.transition(
            "REFUNDED",
            "2026-09-03T03:03:00Z",
            {"doc": "invalid-002"},
        )


def test_transition_record_is_hashed(escrow):
    record = escrow.transition(
        "FUNDED",
        "2026-09-03T04:00:00Z",
        {"doc": "funding-004"},
    )

    expected = domain_hash(
        "ESCROW_TRANSITION",
        {
            "escrow_id": "ESC-001",
            "sequence": 1,
            "previous_state": "CREATED",
            "new_state": "FUNDED",
            "amount": 1000000,
            "currency": "MNT",
        },
    )

    assert record.transition_hash == expected
    assert len(record.transition_hash) == 64


def test_witness_chain_receives_escrow_event(escrow):
    escrow.transition(
        "FUNDED",
        "2026-09-03T05:00:00Z",
        {"doc": "funding-005"},
    )

    assert len(escrow.witness_chain.entries) == 1

    record = escrow.witness_chain.entries[0].record

    assert record.event_type == "ESCROW_TRANSITION"
    assert record.event_id == "ESC-001-1"
    assert record.witness_id == "witness-escrow-01"


def test_each_transition_is_immutable_record(escrow):
    first = escrow.transition(
        "FUNDED",
        "2026-09-03T06:00:00Z",
        {"doc": "funding-006"},
    )

    second = escrow.transition(
        "LOCKED",
        "2026-09-03T06:01:00Z",
        {"doc": "lock-006"},
    )

    assert first.sequence == 1
    assert first.previous_state == "CREATED"
    assert first.new_state == "FUNDED"

    assert second.sequence == 2
    assert second.previous_state == "FUNDED"
    assert second.new_state == "LOCKED"

    assert first.new_state != second.new_state
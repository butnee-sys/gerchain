"""
GerChain V80.2
Adversarial Strict Sequence Tests.

Purpose:
- LOCKED -> ATOMIC_SETTLEMENT -> RELEASED/REFUNDED
  гэсэн яг дарааллыг шалгах.
- Дунд нь sequence gap үүсгэсэн хуурамч бүтэц REJECT болохыг шалгах.
- Settlement-ийн дараах sequence gap мөн REJECT болохыг шалгах.
- Зөв дараалал PASS хэвээр байгааг баталгаажуулах.
"""

from verifier.escrow_semantic_verifier import (
    EscrowSemanticVerifier,
)


def make_record(sequence, event_type):
    return {
        "sequence": sequence,
        "event_type": event_type,
    }


def make_locked_transition(sequence=1):
    return {
        "record": make_record(
            sequence,
            "ESCROW_TRANSITION",
        ),
        "event_payload": {
            "escrow_id": "ESCROW-001",
            "sequence": 2,
            "previous_state": "FUNDED",
            "new_state": "LOCKED",
            "amount": 100,
            "currency": "MNT",
        },
    }


def make_settlement(sequence=2):
    return {
        "record": make_record(
            sequence,
            "ATOMIC_SETTLEMENT",
        ),
        "event_payload": {
            "transaction_id": "TX-001",
            "sequence": 1,
            "source": "BUYER",
            "destination": "SELLER",
            "amount": 100,
            "currency": "MNT",
            "escrow_id": "ESCROW-001",
            "previous_escrow_state": "LOCKED",
            "new_escrow_state": "RELEASED",
            "previous_source_balance": 1000,
            "new_source_balance": 900,
            "previous_destination_balance": 0,
            "new_destination_balance": 100,
        },
    }


def make_released_transition(sequence=3):
    return {
        "record": make_record(
            sequence,
            "ESCROW_TRANSITION",
        ),
        "event_payload": {
            "escrow_id": "ESCROW-001",
            "sequence": 3,
            "previous_state": "LOCKED",
            "new_state": "RELEASED",
            "amount": 100,
            "currency": "MNT",
        },
    }


def test_valid_strict_sequence_passes():
    bundle = {
        "entries": [
            make_locked_transition(1),
            make_settlement(2),
            make_released_transition(3),
        ]
    }

    verifier = EscrowSemanticVerifier()

    assert verifier.verify(bundle) is True


def test_gap_before_settlement_is_rejected():
    """
    LOCKED = sequence 1
    ATOMIC_SETTLEMENT = sequence 3

    sequence 2 байхгүй тул V80.2 REJECT хийх ёстой.
    """

    bundle = {
        "entries": [
            make_locked_transition(1),
            make_settlement(3),
            make_released_transition(4),
        ]
    }

    verifier = EscrowSemanticVerifier()

    assert verifier.verify(bundle) is False


def test_gap_after_settlement_is_rejected():
    """
    LOCKED = sequence 1
    ATOMIC_SETTLEMENT = sequence 2
    RELEASED = sequence 4

    sequence 3 байхгүй тул V80.2 REJECT хийх ёстой.
    """

    bundle = {
        "entries": [
            make_locked_transition(1),
            make_settlement(2),
            make_released_transition(4),
        ]
    }

    verifier = EscrowSemanticVerifier()

    assert verifier.verify(bundle) is False


def test_settlement_without_immediate_locked_transition_is_rejected():
    """
    Settlement-ийн яг өмнөх sequence нь LOCKED биш
    бол REJECT.
    """

    bundle = {
        "entries": [
            make_locked_transition(1),
            {
                "record": make_record(
                    2,
                    "ESCROW_TRANSITION",
                ),
                "event_payload": {
                    "escrow_id": "ESCROW-001",
                    "sequence": 2,
                    "previous_state": "FUNDED",
                    "new_state": "CANCELLED",
                    "amount": 100,
                    "currency": "MNT",
                },
            },
            make_settlement(3),
            make_released_transition(4),
        ]
    }

    verifier = EscrowSemanticVerifier()

    assert verifier.verify(bundle) is False


def test_settlement_without_immediate_terminal_transition_is_rejected():
    """
    ATOMIC_SETTLEMENT-ийн яг дараагийн sequence
    RELEASED/REFUNDED биш бол REJECT.
    """

    bundle = {
        "entries": [
            make_locked_transition(1),
            make_settlement(2),
            {
                "record": make_record(
                    3,
                    "ESCROW_TRANSITION",
                ),
                "event_payload": {
                    "escrow_id": "ESCROW-001",
                    "sequence": 3,
                    "previous_state": "LOCKED",
                    "new_state": "CANCELLED",
                    "amount": 100,
                    "currency": "MNT",
                },
            },
        ]
    }

    verifier = EscrowSemanticVerifier()

    assert verifier.verify(bundle) is False
"""
GerChain V80
Negative Semantic Verification Tests.

Purpose:
- Хүчин төгөлдөр E2E bundle үүсгэх.
- Escrow semantic холбоосыг зориудаар эвдэх.
- Бие даасан шалгагч REJECT хийж байгааг баталгаажуулах.
"""

import json

from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from persistence.serializer import serialize_chain
from verifier.v80_independent_verifier import (
    V80IndependentVerifier,
)
from witness.chain import WitnessChain


def build_valid_bundle():

    initial_state = {
        "value": 0,
        "sequence_counter": 0,
        "initialized": False,
    }

    manifest = {
        "system": "GerChain",
        "version": "V80",
        "purpose": "Negative Semantic Test",
    }

    witness_chain = WitnessChain(
        initial_state=initial_state,
        manifest=manifest,
        witness_id="WITNESS-NEGATIVE-001",
    )

    escrow = EscrowEngine(
        escrow_id="ESCROW-NEGATIVE-001",
        amount=1000,
        currency="MNT",
        witness_chain=witness_chain,
    )

    ledger = MoneyLedger(
        currency="MNT",
    )

    ledger.create_account(
        "BUYER",
        initial_balance=1000,
    )

    ledger.create_account(
        "SELLER",
        initial_balance=0,
    )

    money = MoneyEngine(
        ledger=ledger,
        escrow=escrow,
    )

    escrow.transition(
        target_state="FUNDED",
        timestamp="2026-09-03T03:00:01",
        evidence={
            "type": "FUNDING",
            "reference": "NEG-FUND-001",
        },
    )

    escrow.transition(
        target_state="LOCKED",
        timestamp="2026-09-03T03:00:02",
        evidence={
            "type": "LOCK",
            "reference": "NEG-LOCK-001",
        },
    )

    money.atomic_settlement(
        transaction_id="NEG-TX-001",
        target_state="RELEASED",
        source="BUYER",
        destination="SELLER",
        amount=1000,
        timestamp="2026-09-03T03:00:03",
        evidence={
            "type": "SETTLEMENT",
            "reference": "NEG-SETTLE-001",
        },
    )

    serialized = serialize_chain(
        witness_chain
    )

    return json.loads(
        serialized.decode("utf-8")
    )


def test_tampered_settlement_state_is_rejected():

    bundle = build_valid_bundle()

    entries = bundle["entries"]

    settlement_entry = entries[2]

    settlement_entry[
        "event_payload"
    ][
        "new_escrow_state"
    ] = "REFUNDED"

    verifier = V80IndependentVerifier()

    assert (
        verifier.verify_bundle(
            bundle
        )
        is False
    )


def test_broken_locked_settlement_link_is_rejected():

    bundle = build_valid_bundle()

    entries = bundle["entries"]

    settlement_entry = entries[2]

    settlement_entry[
        "event_payload"
    ][
        "escrow_id"
    ] = "ESCROW-OTHER"

    verifier = V80IndependentVerifier()

    assert (
        verifier.verify_bundle(
            bundle
        )
        is False
    )


def test_tampered_settlement_amount_is_rejected():

    bundle = build_valid_bundle()

    entries = bundle["entries"]

    settlement_entry = entries[2]

    settlement_entry[
        "event_payload"
    ][
        "amount"
    ] = 999

    verifier = V80IndependentVerifier()

    assert (
        verifier.verify_bundle(
            bundle
        )
        is False
    )


def test_broken_settlement_transition_sequence_is_rejected():

    bundle = build_valid_bundle()

    entries = bundle["entries"]

    settlement_entry = entries[2]
    released_entry = entries[3]

    released_entry[
        "record"
    ][
        "sequence"
    ] = 5

    verifier = V80IndependentVerifier()

    assert (
        verifier.verify_bundle(
            bundle
        )
        is False
    )
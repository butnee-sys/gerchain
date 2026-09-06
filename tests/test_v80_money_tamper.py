"""
GerChain V80.3.1
End-to-End Money Tamper Tests.

Purpose:
- Хүчин төгөлдөр мөнгөний settlement үүсгэх.
- Мөнгөний утгыг зориудаар өөрчлөх.
- Криптографийн бүртгэлийг дахин засахгүй.
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
        "purpose": "Money Tamper Test",
    }

    witness_chain = WitnessChain(
        initial_state=initial_state,
        manifest=manifest,
        witness_id="WITNESS-MONEY-TAMPER-001",
    )

    escrow = EscrowEngine(
        escrow_id="ESCROW-MONEY-TAMPER-001",
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
        timestamp="2026-09-03T04:00:01",
        evidence={
            "type": "FUNDING",
            "reference": "TAMPER-FUND-001",
        },
    )

    escrow.transition(
        target_state="LOCKED",
        timestamp="2026-09-03T04:00:02",
        evidence={
            "type": "LOCK",
            "reference": "TAMPER-LOCK-001",
        },
    )

    money.atomic_settlement(
        transaction_id="TAMPER-TX-001",
        target_state="RELEASED",
        source="BUYER",
        destination="SELLER",
        amount=1000,
        timestamp="2026-09-03T04:00:03",
        evidence={
            "type": "SETTLEMENT",
            "reference": "TAMPER-SETTLE-001",
        },
    )

    serialized = serialize_chain(
        witness_chain
    )

    return json.loads(
        serialized.decode("utf-8")
    )


def test_tampered_source_balance_is_rejected():

    bundle = build_valid_bundle()

    settlement = bundle["entries"][2]

    settlement[
        "event_payload"
    ][
        "previous_source_balance"
    ] = 2000

    verifier = V80IndependentVerifier()

    assert (
        verifier.verify_bundle(
            bundle
        )
        is False
    )


def test_tampered_new_source_balance_is_rejected():

    bundle = build_valid_bundle()

    settlement = bundle["entries"][2]

    settlement[
        "event_payload"
    ][
        "new_source_balance"
    ] = 1

    verifier = V80IndependentVerifier()

    assert (
        verifier.verify_bundle(
            bundle
        )
        is False
    )


def test_tampered_destination_balance_is_rejected():

    bundle = build_valid_bundle()

    settlement = bundle["entries"][2]

    settlement[
        "event_payload"
    ][
        "previous_destination_balance"
    ] = 500

    verifier = V80IndependentVerifier()

    assert (
        verifier.verify_bundle(
            bundle
        )
        is False
    )


def test_money_creation_is_rejected_end_to_end():

    bundle = build_valid_bundle()

    settlement = bundle["entries"][2]

    settlement[
        "event_payload"
    ][
        "new_destination_balance"
    ] = 1500

    verifier = V80IndependentVerifier()

    assert (
        verifier.verify_bundle(
            bundle
        )
        is False
    )


def test_money_destruction_is_rejected_end_to_end():

    bundle = build_valid_bundle()

    settlement = bundle["entries"][2]

    settlement[
        "event_payload"
    ][
        "new_source_balance"
    ] = 500

    verifier = V80IndependentVerifier()

    assert (
        verifier.verify_bundle(
            bundle
        )
        is False
    )
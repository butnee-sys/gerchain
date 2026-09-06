"""
GerChain V80.0
Escrow Semantic Verifier Tests.

Purpose:
- Хүчинтэй settlement-ийг PASS болгох.
- Хэшийг дахин тооцоолсон боловч утгын хувьд
  буруу settlement-ийг REJECT хийх.
- Settlement ба Escrow transition-ийн
  хоорондын уялдааг шалгах.
"""

import json

from core.canonical import canonical_bytes
from core.hashing import domain_hash
from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from persistence.serializer import serialize_chain
from verifier.escrow_semantic_verifier import (
    EscrowSemanticVerifier,
)
from witness.chain import WitnessChain


def build_settlement():
    witness_chain = WitnessChain(
        initial_state={
            "initialized": False,
            "sequence_counter": 0,
        },
        manifest={
            "project": "V80-Escrow-Semantic-Verifier",
            "version": "0",
        },
        witness_id="witness-v80-semantic-verifier",
    )

    escrow = EscrowEngine(
        escrow_id="ESC-V80-VERIFY",
        amount=1000000,
        currency="MNT",
        witness_chain=witness_chain,
    )

    ledger = MoneyLedger("MNT")

    ledger.create_account("BUYER", 2000000)
    ledger.create_account("ESCROW", 0)
    ledger.create_account("SELLER", 0)

    money = MoneyEngine(
        ledger=ledger,
        escrow=escrow,
    )

    money.transfer(
        transaction_id="DEP-V80-V",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T12:00:00Z",
        evidence={"type": "deposit"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T12:00:01Z",
        {"type": "funded"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T12:00:02Z",
        {"type": "locked"},
    )

    money.atomic_settlement(
        transaction_id="SET-V80-V",
        target_state="RELEASED",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T12:01:00Z",
        evidence={"type": "delivery-confirmed"},
    )

    return witness_chain


def load_bundle():
    chain = build_settlement()

    return json.loads(
        serialize_chain(chain).decode("utf-8")
    )


def get_settlement(bundle):
    for entry in bundle["entries"]:
        if (
            entry["record"]["event_type"]
            == "ATOMIC_SETTLEMENT"
        ):
            return entry

    raise AssertionError(
        "ATOMIC_SETTLEMENT not found."
    )


def get_transition(bundle):
    for entry in bundle["entries"]:
        if (
            entry["record"]["event_type"]
            == "ESCROW_TRANSITION"
            and entry["event_payload"].get(
                "new_state"
            )
            in {"RELEASED", "REFUNDED"}
        ):
            return entry

    raise AssertionError(
        "Settlement ESCROW_TRANSITION not found."
    )


def rehash_event(entry):
    record = entry["record"]

    event_obj = {
        "sequence": record["sequence"],
        "event_id": record["event_id"],
        "event_type": record["event_type"],
        "timestamp": record["timestamp"],
        "payload": entry["event_payload"],
    }

    record["event_hash"] = domain_hash(
        "WITNESS_EVENT",
        event_obj,
    )


def verify_semantic(bundle):
    return EscrowSemanticVerifier().verify(
        bundle
    )


def test_valid_settlement_passes():
    bundle = load_bundle()

    assert verify_semantic(bundle) is True


def test_rehashed_wrong_previous_state_is_rejected():
    bundle = load_bundle()

    settlement = get_settlement(bundle)

    settlement["event_payload"][
        "previous_escrow_state"
    ] = "CREATED"

    rehash_event(settlement)

    assert verify_semantic(bundle) is False


def test_rehashed_invalid_target_state_is_rejected():
    bundle = load_bundle()

    settlement = get_settlement(bundle)

    settlement["event_payload"][
        "new_escrow_state"
    ] = "CREATED"

    rehash_event(settlement)

    assert verify_semantic(bundle) is False


def test_rehashed_wrong_amount_is_rejected():
    bundle = load_bundle()

    settlement = get_settlement(bundle)

    settlement["event_payload"]["amount"] = 1

    rehash_event(settlement)

    assert verify_semantic(bundle) is False


def test_rehashed_wrong_escrow_identity_is_rejected():
    bundle = load_bundle()

    settlement = get_settlement(bundle)

    settlement["event_payload"]["escrow_id"] = (
        "FORGED-ESCROW"
    )

    rehash_event(settlement)

    assert verify_semantic(bundle) is False


def test_settlement_transition_mismatch_is_rejected():
    bundle = load_bundle()

    settlement = get_settlement(bundle)
    transition = get_transition(bundle)

    settlement["event_payload"][
        "new_escrow_state"
    ] = "REFUNDED"

    rehash_event(settlement)

    assert (
        transition["event_payload"]["new_state"]
        == "RELEASED"
    )

    assert verify_semantic(bundle) is False


def test_settlement_amount_balance_equation_is_checked():
    bundle = load_bundle()

    settlement = get_settlement(bundle)

    settlement["event_payload"][
        "new_source_balance"
    ] = 999999

    rehash_event(settlement)

    assert verify_semantic(bundle) is False


def test_settlement_destination_must_differ_from_source():
    bundle = load_bundle()

    settlement = get_settlement(bundle)

    settlement["event_payload"][
        "destination"
    ] = settlement["event_payload"]["source"]

    rehash_event(settlement)

    assert verify_semantic(bundle) is False


def test_transition_amount_mismatch_is_rejected():
    bundle = load_bundle()

    settlement = get_settlement(bundle)
    transition = get_transition(bundle)

    transition["event_payload"]["amount"] = 1

    rehash_event(transition)

    assert verify_semantic(bundle) is False
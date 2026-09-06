"""
GerChain V80.0
Witness + Escrow Tamper Tests.

Purpose:
- ATOMIC_SETTLEMENT payload өөрчлөгдвөл REJECT хийх.
- Escrow identity өөрчлөгдвөл REJECT хийх.
- Escrow previous state өөрчлөгдвөл REJECT хийх.
- Escrow target state өөрчлөгдвөл REJECT хийх.
- Settlement amount өөрчлөгдвөл REJECT хийх.
- Settlement currency өөрчлөгдвөл REJECT хийх.
- Settlement event hash өөрчлөгдвөл REJECT хийх.
- Энгийн хүчинтэй settlement-ийг PASS болгох.
"""

import json

from core.canonical import canonical_bytes
from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from persistence.serializer import serialize_chain
from verifier.independent_verifier import IndependentVerifier
from witness.chain import WitnessChain


def build_settlement():
    witness_chain = WitnessChain(
        initial_state={
            "initialized": False,
            "sequence_counter": 0,
        },
        manifest={
            "project": "V80-Witness-Escrow-Tamper",
            "version": "0",
        },
        witness_id="witness-v80-tamper-01",
    )

    escrow = EscrowEngine(
        escrow_id="ESC-V80-TAMPER",
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
        transaction_id="DEP-V80-T",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T10:00:00Z",
        evidence={"type": "deposit"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T10:00:01Z",
        {"type": "funded"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T10:00:02Z",
        {"type": "locked"},
    )

    money.atomic_settlement(
        transaction_id="SET-V80-T",
        target_state="RELEASED",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T10:01:00Z",
        evidence={"type": "delivery-confirmed"},
    )

    return witness_chain


def get_tampered_bundle():
    chain = build_settlement()

    bundle = json.loads(
        serialize_chain(chain).decode("utf-8")
    )

    return bundle


def verify_tampered_bundle(bundle):
    tampered_bytes = canonical_bytes(bundle)

    return IndependentVerifier().verify_bytes(
        tampered_bytes
    )


def test_valid_integrated_settlement_passes():
    chain = build_settlement()

    data = serialize_chain(chain)

    assert IndependentVerifier().verify_bytes(
        data
    ) is True


def test_tampered_escrow_id_is_rejected():
    bundle = get_tampered_bundle()

    for entry in bundle["entries"]:
        if (
            entry["record"]["event_type"]
            == "ATOMIC_SETTLEMENT"
        ):
            entry["event_payload"]["escrow_id"] = (
                "FORGED-ESCROW"
            )
            break

    assert verify_tampered_bundle(
        bundle
    ) is False


def test_tampered_previous_escrow_state_is_rejected():
    bundle = get_tampered_bundle()

    for entry in bundle["entries"]:
        if (
            entry["record"]["event_type"]
            == "ATOMIC_SETTLEMENT"
        ):
            entry["event_payload"][
                "previous_escrow_state"
            ] = "CREATED"
            break

    assert verify_tampered_bundle(
        bundle
    ) is False


def test_tampered_new_escrow_state_is_rejected():
    bundle = get_tampered_bundle()

    for entry in bundle["entries"]:
        if (
            entry["record"]["event_type"]
            == "ATOMIC_SETTLEMENT"
        ):
            entry["event_payload"][
                "new_escrow_state"
            ] = "REFUNDED"
            break

    assert verify_tampered_bundle(
        bundle
    ) is False


def test_tampered_settlement_amount_is_rejected():
    bundle = get_tampered_bundle()

    for entry in bundle["entries"]:
        if (
            entry["record"]["event_type"]
            == "ATOMIC_SETTLEMENT"
        ):
            entry["event_payload"]["amount"] = 1
            break

    assert verify_tampered_bundle(
        bundle
    ) is False


def test_tampered_settlement_currency_is_rejected():
    bundle = get_tampered_bundle()

    for entry in bundle["entries"]:
        if (
            entry["record"]["event_type"]
            == "ATOMIC_SETTLEMENT"
        ):
            entry["event_payload"]["currency"] = (
                "USD"
            )
            break

    assert verify_tampered_bundle(
        bundle
    ) is False


def test_tampered_settlement_event_hash_is_rejected():
    bundle = get_tampered_bundle()

    for entry in bundle["entries"]:
        if (
            entry["record"]["event_type"]
            == "ATOMIC_SETTLEMENT"
        ):
            entry["record"]["event_hash"] = (
                "f" * 64
            )
            break

    assert verify_tampered_bundle(
        bundle
    ) is False


def test_tampered_settlement_source_is_rejected():
    bundle = get_tampered_bundle()

    for entry in bundle["entries"]:
        if (
            entry["record"]["event_type"]
            == "ATOMIC_SETTLEMENT"
        ):
            entry["event_payload"]["source"] = (
                "BUYER"
            )
            break

    assert verify_tampered_bundle(
        bundle
    ) is False


def test_tampered_settlement_destination_is_rejected():
    bundle = get_tampered_bundle()

    for entry in bundle["entries"]:
        if (
            entry["record"]["event_type"]
            == "ATOMIC_SETTLEMENT"
        ):
            entry["event_payload"][
                "destination"
            ] = "BUYER"
            break

    assert verify_tampered_bundle(
        bundle
    ) is False
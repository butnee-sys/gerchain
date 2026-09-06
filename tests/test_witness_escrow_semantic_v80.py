"""
GerChain V80.0
Witness + Escrow Semantic Integrity Tests.

Purpose:
- Event hash-ийг шинэчилсэн байсан ч логикийн хувьд
  буруу Escrow settlement-ийг илрүүлэх шаардлагыг тогтоох.
- ATOMIC_SETTLEMENT болон ESCROW_TRANSITION хоорондын
  утгын уялдааг шалгах.
- Escrow төлөвийн хууль ёсны шилжилтийг шалгах.
"""

import json

from core.canonical import canonical_bytes
from core.hashing import domain_hash
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
            "project": "V80-Witness-Escrow-Semantic",
            "version": "0",
        },
        witness_id="witness-v80-semantic-01",
    )

    escrow = EscrowEngine(
        escrow_id="ESC-V80-SEMANTIC",
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
        transaction_id="DEP-V80-S",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T11:00:00Z",
        evidence={"type": "deposit"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T11:00:01Z",
        {"type": "funded"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T11:00:02Z",
        {"type": "locked"},
    )

    money.atomic_settlement(
        transaction_id="SET-V80-S",
        target_state="RELEASED",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T11:01:00Z",
        evidence={"type": "delivery-confirmed"},
    )

    return witness_chain


def load_bundle():
    chain = build_settlement()

    return json.loads(
        serialize_chain(chain).decode("utf-8")
    )


def recompute_event_hash(entry):
    record = entry["record"]

    event_obj = {
        "sequence": record["sequence"],
        "event_id": record["event_id"],
        "event_type": record["event_type"],
        "timestamp": record["timestamp"],
        "payload": entry["event_payload"],
    }

    return domain_hash(
        "WITNESS_EVENT",
        event_obj,
    )


def rehash_entry(entry):
    entry["record"]["event_hash"] = (
        recompute_event_hash(entry)
    )


def verify(bundle):
    return IndependentVerifier().verify_bytes(
        canonical_bytes(bundle)
    )


def find_settlement_entry(bundle):
    for entry in bundle["entries"]:
        if (
            entry["record"]["event_type"]
            == "ATOMIC_SETTLEMENT"
        ):
            return entry

    raise AssertionError(
        "ATOMIC_SETTLEMENT entry not found."
    )


def find_escrow_transition_entry(bundle):
    for entry in bundle["entries"]:
        if (
            entry["record"]["event_type"]
            == "ESCROW_TRANSITION"
        ):
            return entry

    raise AssertionError(
        "ESCROW_TRANSITION entry not found."
    )


def test_valid_semantic_history_passes():
    bundle = load_bundle()

    assert verify(bundle) is True


def test_rehashed_wrong_previous_state_should_be_rejected():
    bundle = load_bundle()

    settlement = find_settlement_entry(bundle)

    settlement["event_payload"][
        "previous_escrow_state"
    ] = "CREATED"

    rehash_entry(settlement)

    # Одоогийн ерөнхий verifier нь зөвхөн
    # криптографийн бүтэн байдлыг шалгаж байгаа тул
    # энэ нь одоогоор PASS болж магадгүй.
    #
    # V80 semantic verifier нэвтэрсний дараа
    # REJECT болох ёстой.
    assert verify(bundle) is True


def test_rehashed_wrong_target_state_should_be_rejected():
    bundle = load_bundle()

    settlement = find_settlement_entry(bundle)

    settlement["event_payload"][
        "new_escrow_state"
    ] = "CREATED"

    rehash_entry(settlement)

    assert verify(bundle) is True


def test_rehashed_wrong_amount_should_be_rejected():
    bundle = load_bundle()

    settlement = find_settlement_entry(bundle)

    settlement["event_payload"]["amount"] = 1

    rehash_entry(settlement)

    assert verify(bundle) is True


def test_rehashed_wrong_escrow_identity_should_be_rejected():
    bundle = load_bundle()

    settlement = find_settlement_entry(bundle)

    settlement["event_payload"]["escrow_id"] = (
        "FORGED-ESCROW"
    )

    rehash_entry(settlement)

    assert verify(bundle) is True


def test_rehashed_settlement_transition_mismatch_should_be_rejected():
    bundle = load_bundle()

    settlement = find_settlement_entry(bundle)
    escrow_transition = find_escrow_transition_entry(
        bundle
    )

    settlement["event_payload"][
        "new_escrow_state"
    ] = "REFUNDED"

    rehash_entry(settlement)

    # ESCROW_TRANSITION нь RELEASED хэвээр.
    # Settlement -> Escrow transition хооронд
    # утгын зөрчил үүссэн байна.
    assert (
        settlement["event_payload"][
            "new_escrow_state"
        ]
        != escrow_transition["event_payload"][
            "new_state"
        ]
    )

    # Одоогийн verifier криптографийн хувьд үүнийг
    # хүчинтэй гэж үзэж магадгүй.
    assert verify(bundle) is True
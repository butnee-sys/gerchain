"""
GerChain V80.0
Full Independent Escrow Verification Tests.

Purpose:
- Witness криптографийн шалгалт.
- Escrow semantic шалгалт.
- Хоёр шалгалтыг нэг бүрэн бие даасан
  verification урсгалд нэгтгэх.
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
from verifier.independent_verifier import (
    IndependentVerifier,
)
from witness.chain import WitnessChain


def build_settlement():
    witness_chain = WitnessChain(
        initial_state={
            "initialized": False,
            "sequence_counter": 0,
        },
        manifest={
            "project": "V80-Full-Independent",
            "version": "0",
        },
        witness_id="witness-v80-full-01",
    )

    escrow = EscrowEngine(
        escrow_id="ESC-V80-FULL",
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
        transaction_id="DEP-V80-FULL",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T14:00:00Z",
        evidence={"type": "deposit"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T14:00:01Z",
        {"type": "funded"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T14:00:02Z",
        {"type": "locked"},
    )

    money.atomic_settlement(
        transaction_id="SET-V80-FULL",
        target_state="RELEASED",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T14:01:00Z",
        evidence={"type": "delivery-confirmed"},
    )

    return witness_chain


def load_bundle():
    chain = build_settlement()

    return json.loads(
        serialize_chain(chain).decode("utf-8")
    )


def verify_full(bundle):
    witness_ok = IndependentVerifier().verify_bundle(
        bundle
    )

    semantic_ok = EscrowSemanticVerifier().verify(
        bundle
    )

    return witness_ok and semantic_ok


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
        "Settlement transition not found."
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


def test_full_valid_verification_passes():
    bundle = load_bundle()

    assert verify_full(bundle) is True


def test_full_verification_rejects_event_tamper():
    bundle = load_bundle()

    settlement = get_settlement(bundle)

    settlement["event_payload"]["amount"] = 1

    # Хуучин event_hash хэвээр үлдэнэ.
    assert verify_full(bundle) is False


def test_full_verification_rejects_rehashed_semantic_tamper():
    bundle = load_bundle()

    settlement = get_settlement(bundle)

    settlement["event_payload"][
        "previous_escrow_state"
    ] = "CREATED"

    # Хуурамч payload-д шинэ зөв хэш өгнө.
    rehash_event(settlement)

    # Криптографийн verifier дангаараа PASS хийж
    # болох боловч semantic verifier REJECT хийнэ.
    assert (
        IndependentVerifier().verify_bundle(
            bundle
        )
        is True
    )

    assert (
        EscrowSemanticVerifier().verify(
            bundle
        )
        is False
    )

    assert verify_full(bundle) is False


def test_full_verification_rejects_transition_mismatch():
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

    assert verify_full(bundle) is False


def test_full_verification_rejects_wrong_amount_equation():
    bundle = load_bundle()

    settlement = get_settlement(bundle)

    settlement["event_payload"][
        "new_source_balance"
    ] = 123456

    rehash_event(settlement)

    assert verify_full(bundle) is False


def test_full_verification_accepts_serialized_roundtrip():
    chain = build_settlement()

    serialized = serialize_chain(chain)

    bundle = json.loads(
        serialized.decode("utf-8")
    )

    assert verify_full(bundle) is True


def test_full_verification_rejects_manifest_tamper():
    bundle = load_bundle()

    bundle["manifest"]["version"] = "FORGED"

    assert verify_full(bundle) is False


def test_full_verification_rejects_escrow_identity_tamper():
    bundle = load_bundle()

    settlement = get_settlement(bundle)

    settlement["event_payload"][
        "escrow_id"
    ] = "FORGED-ESCROW"

    rehash_event(settlement)

    assert verify_full(bundle) is False


def test_full_verification_rejects_invalid_target():
    bundle = load_bundle()

    settlement = get_settlement(bundle)

    settlement["event_payload"][
        "new_escrow_state"
    ] = "CANCELLED"

    rehash_event(settlement)

    assert verify_full(bundle) is False


def test_full_verification_rejects_transition_amount_tamper():
    bundle = load_bundle()

    transition = get_transition(bundle)

    transition["event_payload"]["amount"] = 1

    rehash_event(transition)

    assert verify_full(bundle) is False
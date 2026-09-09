"""
GerChain V80.1
Escrow Chain Semantic Integrity Tests.

Purpose:
- ATOMIC_SETTLEMENT нь өмнөх LOCKED escrow transition-тэй
  логикийн хувьд нийцэж байгаа эсэхийг шалгах.
- escrow_id, amount, currency-ийн уялдааг шалгах.
- Settlement-ийн өмнөх болон дараах state transition-ийг
  дарааллаар нь шалгах.
"""

from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from persistence.serializer import serialize_chain
from verifier.v80_independent_verifier import (
    V80IndependentVerifier,
)
from witness.chain import WitnessChain

from core.hashing import domain_hash


def build_valid_bundle():
    initial_state = {
        "value": 0,
        "sequence_counter": 0,
        "initialized": False,
    }

    manifest = {
        "version": "V80.1",
        "system": "GerChain",
        "purpose": "Escrow Settlement",
    }

    money_state = {
        "currency": "MNT",
        "balances": {
            "BUYER": 1000,
            "SELLER": 0,
        },
    }

    witness_chain = WitnessChain(
        initial_state=initial_state,
        manifest=manifest,
        witness_id="WITNESS-001",
        initial_money_state=money_state,
    )

    commitment = witness_chain.get_initial_money_commitment()

    witness_chain.append_event(
        event_id="INITIAL-MONEY-V801-001",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T09:59:59Z",
        payload={
            "state": commitment["state"],
            "state_hash": commitment["state_hash"],
        },
        evidence={
            "type": "INITIAL_MONEY_COMMITMENT",
            "reference": "INITIAL-MONEY-V801-001",
        },
    )

    escrow = EscrowEngine(
        escrow_id="ESCROW-001",
        amount=100,
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
        timestamp="2026-09-03T10:00:00Z",
        evidence={
            "type": "funding",
        },
    )

    escrow.transition(
        target_state="LOCKED",
        timestamp="2026-09-03T10:01:00Z",
        evidence={
            "type": "locking",
        },
    )

    money.atomic_settlement(
        transaction_id="TX-001",
        target_state="RELEASED",
        source="BUYER",
        destination="SELLER",
        amount=100,
        timestamp="2026-09-03T10:02:00Z",
        evidence={
            "type": "settlement",
        },
    )

    return __import__("json").loads(
        serialize_chain(witness_chain).decode("utf-8")
    )


def find_entry(bundle, event_type):
    for entry in bundle["entries"]:
        if entry["record"]["event_type"] == event_type:
            return entry

    raise AssertionError(
        f"Missing event type: {event_type}"
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

    record["event_hash"] = domain_hash(
        "WITNESS_EVENT",
        event_obj,
    )


def test_valid_locked_to_settlement_chain_passes():
    bundle = build_valid_bundle()

    verifier = V80IndependentVerifier()

    assert verifier.verify_bundle(bundle) is True


def test_settlement_requires_preceding_locked_transition():
    bundle = build_valid_bundle()

    settlement = find_entry(
        bundle,
        "ATOMIC_SETTLEMENT",
    )

    locked = None

    for entry in bundle["entries"]:
        payload = entry["event_payload"]

        if (
            entry["record"]["event_type"]
            == "ESCROW_TRANSITION"
            and payload.get("new_state") == "LOCKED"
            and entry["record"]["sequence"]
            < settlement["record"]["sequence"]
        ):
            locked = entry

    assert locked is not None


def test_settlement_escrow_id_matches_locked_escrow():
    bundle = build_valid_bundle()

    settlement = find_entry(
        bundle,
        "ATOMIC_SETTLEMENT",
    )

    locked = None

    for entry in bundle["entries"]:
        payload = entry["event_payload"]

        if (
            entry["record"]["event_type"]
            == "ESCROW_TRANSITION"
            and payload.get("new_state") == "LOCKED"
            and entry["record"]["sequence"]
            < settlement["record"]["sequence"]
        ):
            locked = entry

    assert settlement["event_payload"]["escrow_id"] == (
        locked["event_payload"]["escrow_id"]
    )


def test_rehashed_settlement_with_wrong_locked_amount_is_rejected():
    bundle = build_valid_bundle()

    settlement = find_entry(
        bundle,
        "ATOMIC_SETTLEMENT",
    )

    locked = None

    for entry in bundle["entries"]:
        payload = entry["event_payload"]

        if (
            entry["record"]["event_type"]
            == "ESCROW_TRANSITION"
            and payload.get("new_state") == "LOCKED"
            and entry["record"]["sequence"]
            < settlement["record"]["sequence"]
        ):
            locked = entry

    assert locked is not None

    locked["event_payload"]["amount"] = 999
    recompute_event_hash(locked)

    verifier = V80IndependentVerifier()

    assert verifier.verify_bundle(bundle) is False


def test_rehashed_settlement_with_wrong_locked_currency_is_rejected():
    bundle = build_valid_bundle()

    settlement = find_entry(
        bundle,
        "ATOMIC_SETTLEMENT",
    )

    locked = None

    for entry in bundle["entries"]:
        payload = entry["event_payload"]

        if (
            entry["record"]["event_type"]
            == "ESCROW_TRANSITION"
            and payload.get("new_state") == "LOCKED"
            and entry["record"]["sequence"]
            < settlement["record"]["sequence"]
        ):
            locked = entry

    assert locked is not None

    locked["event_payload"]["currency"] = "USD"
    recompute_event_hash(locked)

    verifier = V80IndependentVerifier()

    assert verifier.verify_bundle(bundle) is False
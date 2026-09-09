"""
GerChain V80.0
Tests for Unified Independent Verifier.
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
        "version": "V80.0",
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
        event_id="INITIAL-MONEY-V80-001",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T09:59:59Z",
        payload={
            "state": commitment["state"],
            "state_hash": commitment["state_hash"],
        },
        evidence={
            "type": "INITIAL_MONEY_COMMITMENT",
            "reference": "INITIAL-MONEY-V80-001",
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
            "source": "test",
            "type": "funding",
        },
    )

    escrow.transition(
        target_state="LOCKED",
        timestamp="2026-09-03T10:01:00Z",
        evidence={
            "source": "test",
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
            "source": "test",
            "type": "settlement",
        },
    )

    data = serialize_chain(witness_chain)

    return json.loads(
        data.decode("utf-8")
    )


def recompute_event_hash(entry):
    from core.hashing import domain_hash

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


def test_valid_bundle_passes():
    bundle = build_valid_bundle()

    verifier = V80IndependentVerifier()

    assert verifier.verify_bundle(bundle) is True


def test_valid_bundle_report_is_all_pass():
    bundle = build_valid_bundle()

    verifier = V80IndependentVerifier()

    report = verifier.verify_with_report(bundle)

    assert report["version"] == "V80.0"
    assert report["witness_cryptographic"] is True
    assert report["escrow_semantic"] is True
    assert report["overall"] is True


def test_cryptographic_tampering_is_rejected():
    bundle = build_valid_bundle()

    bundle["entries"][0]["event_payload"]["value"] = 999999

    verifier = V80IndependentVerifier()

    assert verifier.verify_bundle(bundle) is False


def test_manifest_tampering_is_rejected():
    bundle = build_valid_bundle()

    bundle["manifest"]["purpose"] = "TAMPERED"

    verifier = V80IndependentVerifier()

    assert verifier.verify_bundle(bundle) is False


def test_rehashed_semantic_tampering_is_rejected():
    bundle = build_valid_bundle()

    target = find_settlement_entry(bundle)

    target["event_payload"][
        "previous_escrow_state"
    ] = "FUNDED"

    recompute_event_hash(target)

    verifier = V80IndependentVerifier()

    assert verifier.verify_bundle(bundle) is False


def test_rehashed_wrong_amount_is_rejected():
    bundle = build_valid_bundle()

    target = find_settlement_entry(bundle)

    target["event_payload"]["amount"] = 200

    recompute_event_hash(target)

    verifier = V80IndependentVerifier()

    assert verifier.verify_bundle(bundle) is False


def test_rehashed_wrong_escrow_identity_is_rejected():
    bundle = build_valid_bundle()

    target = find_settlement_entry(bundle)

    target["event_payload"]["escrow_id"] = (
        "FAKE-ESCROW"
    )

    recompute_event_hash(target)

    verifier = V80IndependentVerifier()

    assert verifier.verify_bundle(bundle) is False


def test_invalid_bytes_are_rejected():
    verifier = V80IndependentVerifier()

    assert verifier.verify_bytes(
        b"not valid json"
    ) is False


def test_non_dict_bundle_is_rejected():
    verifier = V80IndependentVerifier()

    assert verifier.verify_bundle(
        {"invalid": True}
    ) is False
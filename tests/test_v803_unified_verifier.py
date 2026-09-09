"""
GerChain V80.3
Unified Independent Verifier Tests.
"""

import json

from core.hashing import domain_hash
from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from persistence.serializer import serialize_chain
from verifier.v80_independent_verifier import V80IndependentVerifier
from witness.chain import WitnessChain


def build_valid_bundle():
    initial_state = {
        "value": 0,
        "sequence_counter": 0,
        "initialized": False,
    }

    manifest = {
        "version": "V80.3",
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
        event_id="INITIAL-MONEY-ESCROW-001",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T09:59:59Z",
        payload={
            "state": commitment["state"],
            "state_hash": commitment["state_hash"],
        },
        evidence={
            "type": "INITIAL_MONEY_COMMITMENT",
            "reference": "INITIAL-MONEY-ESCROW-001",
        },
    )

    escrow = EscrowEngine(
        escrow_id="ESCROW-001",
        amount=100,
        currency="MNT",
        witness_chain=witness_chain,
    )

    ledger = MoneyLedger(currency="MNT")

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
        evidence={"type": "funding"},
    )

    escrow.transition(
        target_state="LOCKED",
        timestamp="2026-09-03T10:01:00Z",
        evidence={"type": "locking"},
    )

    money.atomic_settlement(
        transaction_id="TX-001",
        target_state="RELEASED",
        source="BUYER",
        destination="SELLER",
        amount=100,
        timestamp="2026-09-03T10:02:00Z",
        evidence={"type": "settlement"},
    )

    return json.loads(
        serialize_chain(witness_chain).decode("utf-8")
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


def find_entry(bundle, event_type):
    for entry in bundle["entries"]:
        if entry["record"]["event_type"] == event_type:
            return entry

    raise AssertionError(
        f"Missing event type: {event_type}"
    )


def test_v803_valid_bundle_passes():
    bundle = build_valid_bundle()

    verifier = V80IndependentVerifier()

    assert verifier.verify_bundle(bundle) is True


def test_v803_report_contains_three_independent_layers():
    bundle = build_valid_bundle()

    verifier = V80IndependentVerifier()

    report = verifier.verify_with_report(bundle)

    assert report["version"] == "V80.0"
    assert report["money_semantic_version"] == "V80.3"
    assert report["witness_cryptographic"] is True
    assert report["escrow_semantic"] is True
    assert report["money_semantic"] is True
    assert report["overall"] is True


def test_v803_wrong_money_amount_is_rejected():
    bundle = build_valid_bundle()

    settlement = find_entry(
        bundle,
        "ATOMIC_SETTLEMENT",
    )

    settlement["event_payload"]["amount"] = 999

    recompute_event_hash(settlement)

    verifier = V80IndependentVerifier()

    assert verifier.verify_bundle(bundle) is False


def test_v803_wrong_source_balance_is_rejected():
    bundle = build_valid_bundle()

    settlement = find_entry(
        bundle,
        "ATOMIC_SETTLEMENT",
    )

    settlement["event_payload"][
        "new_source_balance"
    ] = 950

    recompute_event_hash(settlement)

    verifier = V80IndependentVerifier()

    assert verifier.verify_bundle(bundle) is False


def test_v803_wrong_destination_balance_is_rejected():
    bundle = build_valid_bundle()

    settlement = find_entry(
        bundle,
        "ATOMIC_SETTLEMENT",
    )

    settlement["event_payload"][
        "new_destination_balance"
    ] = 50

    recompute_event_hash(settlement)

    verifier = V80IndependentVerifier()

    assert verifier.verify_bundle(bundle) is False
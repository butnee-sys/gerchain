"""
GerChain V80
End-to-End Escrow + Money + Witness + Independent Verification Test.

Flow:

CREATED
    ↓
FUNDED
    ↓
LOCKED
    ↓
ATOMIC_SETTLEMENT
    ↓
RELEASED
    ↓
Independent Verification
"""

from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from persistence.serializer import serialize_chain
from verifier.v80_independent_verifier import (
    V80IndependentVerifier,
)
from witness.chain import WitnessChain


def build_end_to_end_system():
    initial_state = {
        "value": 0,
        "sequence_counter": 0,
        "initialized": False,
    }

    manifest = {
        "system": "GerChain",
        "version": "V80",
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
        event_id="INITIAL-MONEY-V80-E2E-001",
        event_type="INITIAL_MONEY_STATE",
        timestamp="2026-09-03T00:00:00Z",
        payload={
            "state": commitment["state"],
            "state_hash": commitment["state_hash"],
        },
        evidence={
            "type": "INITIAL_MONEY_COMMITMENT",
            "reference": "INITIAL-MONEY-V80-E2E-001",
        },
    )

    escrow = EscrowEngine(
        escrow_id="ESCROW-001",
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

    return (
        witness_chain,
        escrow,
        ledger,
        money,
    )


def test_v80_end_to_end_released_settlement():

    (
        witness_chain,
        escrow,
        ledger,
        money,
    ) = build_end_to_end_system()

    # CREATED -> FUNDED
    escrow.transition(
        target_state="FUNDED",
        timestamp="2026-09-03T00:00:01",
        evidence={
            "type": "FUNDING",
            "reference": "FUND-001",
        },
    )

    # FUNDED -> LOCKED
    escrow.transition(
        target_state="LOCKED",
        timestamp="2026-09-03T00:00:02",
        evidence={
            "type": "LOCK",
            "reference": "LOCK-001",
        },
    )

    # LOCKED -> ATOMIC_SETTLEMENT -> RELEASED
    money.atomic_settlement(
        transaction_id="TX-001",
        target_state="RELEASED",
        source="BUYER",
        destination="SELLER",
        amount=1000,
        timestamp="2026-09-03T00:00:03",
        evidence={
            "type": "SETTLEMENT",
            "reference": "SETTLE-001",
        },
    )

    # Escrow final state
    assert escrow.get_state()["state"] == "RELEASED"

    # Money final state
    assert ledger.get_balance("BUYER") == 0
    assert ledger.get_balance("SELLER") == 1000

    # Expected Witness sequence:
    #
    # 1 INITIAL_MONEY_STATE
    # 2 FUNDED
    # 3 LOCKED
    # 4 ATOMIC_SETTLEMENT
    # 5 RELEASED
    assert len(witness_chain.entries) == 5

    assert (
        witness_chain.entries[0].record.event_type
        == "INITIAL_MONEY_STATE"
    )

    assert (
        witness_chain.entries[1].record.event_type
        == "ESCROW_TRANSITION"
    )

    assert (
        witness_chain.entries[2].record.event_type
        == "ESCROW_TRANSITION"
    )

    assert (
        witness_chain.entries[3].record.event_type
        == "ATOMIC_SETTLEMENT"
    )

    assert (
        witness_chain.entries[4].record.event_type
        == "ESCROW_TRANSITION"
    )

    # Serialize the actual WitnessChain.
    serialized = serialize_chain(
        witness_chain
    )

    # Independent verification.
    verifier = V80IndependentVerifier()

    assert verifier.verify_bytes(
        serialized
    ) is True


def test_v80_end_to_end_released_report():

    (
        witness_chain,
        escrow,
        ledger,
        money,
    ) = build_end_to_end_system()

    escrow.transition(
        target_state="FUNDED",
        timestamp="2026-09-03T00:00:01",
        evidence={
            "type": "FUNDING",
            "reference": "FUND-002",
        },
    )

    escrow.transition(
        target_state="LOCKED",
        timestamp="2026-09-03T00:00:02",
        evidence={
            "type": "LOCK",
            "reference": "LOCK-002",
        },
    )

    money.atomic_settlement(
        transaction_id="TX-002",
        target_state="RELEASED",
        source="BUYER",
        destination="SELLER",
        amount=1000,
        timestamp="2026-09-03T00:00:03",
        evidence={
            "type": "SETTLEMENT",
            "reference": "SETTLE-002",
        },
    )

    serialized = serialize_chain(
        witness_chain
    )

    import json

    bundle = json.loads(
        serialized.decode("utf-8")
    )

    verifier = V80IndependentVerifier()

    report = verifier.verify_with_report(
        bundle
    )

    assert report["witness_cryptographic"] is True
    assert report["escrow_semantic"] is True
    assert report["money_semantic"] is True
    assert report["overall"] is True
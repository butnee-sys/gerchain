"""
GerChain V80
End-to-End Refund Settlement Test.

Flow:

CREATED
    ↓
FUNDED
    ↓
LOCKED
    ↓
ATOMIC_SETTLEMENT
    ↓
REFUNDED
    ↓
Money Ledger
    ↓
Witness Chain
    ↓
Serialization
    ↓
Independent Verification
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


def build_refund_system():

    initial_state = {
        "value": 0,
        "sequence_counter": 0,
        "initialized": False,
    }

    manifest = {
        "system": "GerChain",
        "version": "V80",
        "purpose": "Escrow Refund Settlement",
    }

    witness_chain = WitnessChain(
        initial_state=initial_state,
        manifest=manifest,
        witness_id="WITNESS-REFUND-001",
    )

    escrow = EscrowEngine(
        escrow_id="ESCROW-REFUND-001",
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
        "ESCROW",
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


def test_v80_end_to_end_refund():

    (
        witness_chain,
        escrow,
        ledger,
        money,
    ) = build_refund_system()

    # CREATED -> FUNDED
    escrow.transition(
        target_state="FUNDED",
        timestamp="2026-09-03T01:00:01",
        evidence={
            "type": "FUNDING",
            "reference": "REFUND-FUND-001",
        },
    )

    # FUNDED -> LOCKED
    escrow.transition(
        target_state="LOCKED",
        timestamp="2026-09-03T01:00:02",
        evidence={
            "type": "LOCK",
            "reference": "REFUND-LOCK-001",
        },
    )

    # LOCKED -> ATOMIC_SETTLEMENT -> REFUNDED
    money.atomic_settlement(
        transaction_id="REFUND-TX-001",
        target_state="REFUNDED",
        source="BUYER",
        destination="ESCROW",
        amount=1000,
        timestamp="2026-09-03T01:00:03",
        evidence={
            "type": "REFUND_SETTLEMENT",
            "reference": "REFUND-SETTLE-001",
        },
    )

    # Эскроу эцсийн төлөв
    assert (
        escrow.get_state()["state"]
        == "REFUNDED"
    )

    # Мөнгөний эцсийн төлөв
    assert (
        ledger.get_balance("BUYER")
        == 0
    )

    assert (
        ledger.get_balance("ESCROW")
        == 1000
    )

    # Witness sequence:
    #
    # 1 FUNDED
    # 2 LOCKED
    # 3 ATOMIC_SETTLEMENT
    # 4 REFUNDED
    assert len(
        witness_chain.entries
    ) == 4

    assert (
        witness_chain.entries[0]
        .record.event_type
        == "ESCROW_TRANSITION"
    )

    assert (
        witness_chain.entries[1]
        .record.event_type
        == "ESCROW_TRANSITION"
    )

    assert (
        witness_chain.entries[2]
        .record.event_type
        == "ATOMIC_SETTLEMENT"
    )

    assert (
        witness_chain.entries[3]
        .record.event_type
        == "ESCROW_TRANSITION"
    )

    # Сериалчлал
    serialized = serialize_chain(
        witness_chain
    )

    # Бие даасан шалгалт
    verifier = V80IndependentVerifier()

    assert (
        verifier.verify_bytes(
            serialized
        )
        is True
    )


def test_v80_end_to_end_refund_report():

    (
        witness_chain,
        escrow,
        ledger,
        money,
    ) = build_refund_system()

    escrow.transition(
        target_state="FUNDED",
        timestamp="2026-09-03T02:00:01",
        evidence={
            "type": "FUNDING",
            "reference": "REFUND-FUND-002",
        },
    )

    escrow.transition(
        target_state="LOCKED",
        timestamp="2026-09-03T02:00:02",
        evidence={
            "type": "LOCK",
            "reference": "REFUND-LOCK-002",
        },
    )

    money.atomic_settlement(
        transaction_id="REFUND-TX-002",
        target_state="REFUNDED",
        source="BUYER",
        destination="ESCROW",
        amount=1000,
        timestamp="2026-09-03T02:00:03",
        evidence={
            "type": "REFUND_SETTLEMENT",
            "reference": "REFUND-SETTLE-002",
        },
    )

    serialized = serialize_chain(
        witness_chain
    )

    bundle = json.loads(
        serialized.decode("utf-8")
    )

    verifier = V80IndependentVerifier()

    report = (
        verifier.verify_with_report(
            bundle
        )
    )

    assert (
        report["witness_cryptographic"]
        is True
    )

    assert (
        report["escrow_semantic"]
        is True
    )

    assert (
        report["money_semantic"]
        is True
    )

    assert (
        report["overall"]
        is True
    )
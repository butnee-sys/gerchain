"""
GerChain V80.0
Witness + Escrow Integration Tests.

Purpose:
- Atomic settlement нь WitnessChain-тэй зөв холбогдсон эсэхийг шалгах.
- Escrow transition ба settlement event дарааллыг баталгаажуулах.
- Settlement event payload нь Escrow төлөвийн шилжилттэй
  криптографийн хувьд холбогдсон эсэхийг шалгах.
- IndependentVerifier бүх Witness history-г дахин тооцоолж
  баталгаажуулж чадах эсэхийг шалгах.
"""

from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from verifier.independent_verifier import IndependentVerifier
from witness.chain import WitnessChain


def build_settlement():
    witness_chain = WitnessChain(
        initial_state={
            "initialized": False,
            "sequence_counter": 0,
        },
        manifest={
            "project": "V80-Witness-Escrow-Integration",
            "version": "0",
        },
        witness_id="witness-v80-01",
    )

    escrow = EscrowEngine(
        escrow_id="ESC-V80",
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

    return witness_chain, escrow, ledger, money


def fund_and_lock(
    witness_chain,
    escrow,
    money,
):
    money.transfer(
        transaction_id="DEP-V80",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T09:00:00Z",
        evidence={"type": "deposit"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T09:00:01Z",
        {"type": "funded"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T09:00:02Z",
        {"type": "locked"},
    )


def test_atomic_settlement_creates_witness_event():
    witness_chain, escrow, ledger, money = build_settlement()

    fund_and_lock(
        witness_chain,
        escrow,
        money,
    )

    before = len(witness_chain.entries)

    money.atomic_settlement(
        transaction_id="SET-V80-001",
        target_state="RELEASED",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T09:01:00Z",
        evidence={"type": "delivery-confirmed"},
    )

    assert len(witness_chain.entries) == before + 2

    settlement_entry = witness_chain.entries[-2]
    escrow_entry = witness_chain.entries[-1]

    assert (
        settlement_entry.record.event_type
        == "ATOMIC_SETTLEMENT"
    )

    assert (
        escrow_entry.record.event_type
        == "ESCROW_TRANSITION"
    )


def test_settlement_event_contains_escrow_identity():
    witness_chain, escrow, ledger, money = build_settlement()

    fund_and_lock(
        witness_chain,
        escrow,
        money,
    )

    money.atomic_settlement(
        transaction_id="SET-V80-002",
        target_state="RELEASED",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T09:02:00Z",
        evidence={"type": "delivery-confirmed"},
    )

    settlement_entry = witness_chain.entries[-2]

    payload = settlement_entry.event_payload

    assert payload["escrow_id"] == "ESC-V80"
    assert payload["previous_escrow_state"] == "LOCKED"
    assert payload["new_escrow_state"] == "RELEASED"
    assert payload["amount"] == 1000000
    assert payload["currency"] == "MNT"


def test_independent_verifier_accepts_integrated_history():
    witness_chain, escrow, ledger, money = build_settlement()

    fund_and_lock(
        witness_chain,
        escrow,
        money,
    )

    money.atomic_settlement(
        transaction_id="SET-V80-003",
        target_state="RELEASED",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T09:03:00Z",
        evidence={"type": "delivery-confirmed"},
    )

    from persistence.serializer import serialize_chain

    serialized = serialize_chain(
        witness_chain
    )

    verifier = IndependentVerifier()

    assert verifier.verify_bytes(
        serialized
    )


def test_escrow_settlement_and_witness_tip_are_consistent():
    witness_chain, escrow, ledger, money = build_settlement()

    fund_and_lock(
        witness_chain,
        escrow,
        money,
    )

    money.atomic_settlement(
        transaction_id="SET-V80-004",
        target_state="RELEASED",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T09:04:00Z",
        evidence={"type": "delivery-confirmed"},
    )

    assert escrow.get_state()["state"] == "RELEASED"

    final_entry = witness_chain.entries[-1]

    assert (
        final_entry.record.event_type
        == "ESCROW_TRANSITION"
    )

    assert (
        final_entry.event_payload["new_state"]
        == "RELEASED"
    )

    verifier = IndependentVerifier()

    serialized = __import__(
        "persistence.serializer",
        fromlist=["serialize_chain"],
    ).serialize_chain(
        witness_chain
    )

    assert verifier.verify_bytes(
        serialized
    )
"""
GerChain V80.0
Witness Rollback Integrity Tests.

Purpose:
- Амжилтгүй atomic settlement үед WitnessChain өөрчлөгдөхгүй
  байх шаардлагыг тогтоох.
- Witness entries-ийн тоо өөрчлөгдөхгүй байх.
- Witness current state өөрчлөгдөхгүй байх.
- Witness current state hash өөрчлөгдөхгүй байх.
- Алдаа гарсны дараа дараагийн хүчинтэй settlement ажиллах
  боломжтой хэвээр байх.
"""

import pytest

from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from witness.chain import WitnessChain


def build_locked_escrow():
    witness_chain = WitnessChain(
        initial_state={
            "initialized": False,
            "sequence_counter": 0,
        },
        manifest={
            "project": "V80-Witness-Rollback",
            "version": "0",
        },
        witness_id="witness-v80-rollback-01",
    )

    escrow = EscrowEngine(
        escrow_id="ESC-V80-ROLLBACK",
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
        transaction_id="DEP-V80-R",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T13:00:00Z",
        evidence={"type": "deposit"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T13:00:01Z",
        {"type": "funded"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T13:00:02Z",
        {"type": "locked"},
    )

    return witness_chain, escrow, ledger, money


def test_failed_settlement_does_not_add_witness_entry():
    witness_chain, escrow, ledger, money = (
        build_locked_escrow()
    )

    before_count = len(witness_chain.entries)

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-V80-001",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=2000000,
            timestamp="2026-09-03T13:01:00Z",
            evidence={"type": "failed"},
        )

    assert len(witness_chain.entries) == before_count


def test_failed_settlement_does_not_change_witness_state():
    witness_chain, escrow, ledger, money = (
        build_locked_escrow()
    )

    before_state = witness_chain.current_state.copy()

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-V80-002",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=2000000,
            timestamp="2026-09-03T13:02:00Z",
            evidence={"type": "failed"},
        )

    assert (
        witness_chain.current_state
        == before_state
    )


def test_failed_settlement_does_not_change_witness_state_hash():
    witness_chain, escrow, ledger, money = (
        build_locked_escrow()
    )

    before_hash = witness_chain.current_state_hash

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-V80-003",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=2000000,
            timestamp="2026-09-03T13:03:00Z",
            evidence={"type": "failed"},
        )

    assert (
        witness_chain.current_state_hash
        == before_hash
    )


def test_failed_settlement_does_not_change_escrow_state():
    witness_chain, escrow, ledger, money = (
        build_locked_escrow()
    )

    before_state = escrow.get_state()

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-V80-004",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=2000000,
            timestamp="2026-09-03T13:04:00Z",
            evidence={"type": "failed"},
        )

    assert escrow.get_state() == before_state


def test_failed_settlement_does_not_change_balances():
    witness_chain, escrow, ledger, money = (
        build_locked_escrow()
    )

    before_balances = dict(ledger.balances)

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-V80-005",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=2000000,
            timestamp="2026-09-03T13:05:00Z",
            evidence={"type": "failed"},
        )

    assert ledger.balances == before_balances


def test_failed_settlement_does_not_create_money_record():
    witness_chain, escrow, ledger, money = (
        build_locked_escrow()
    )

    before_records = len(money.records)

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-V80-006",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=2000000,
            timestamp="2026-09-03T13:06:00Z",
            evidence={"type": "failed"},
        )

    assert len(money.records) == before_records


def test_invalid_target_does_not_change_witness_history():
    witness_chain, escrow, ledger, money = (
        build_locked_escrow()
    )

    before_count = len(witness_chain.entries)
    before_hash = witness_chain.current_state_hash

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-V80-007",
            target_state="CANCELLED",
            source="ESCROW",
            destination="SELLER",
            amount=1000000,
            timestamp="2026-09-03T13:07:00Z",
            evidence={"type": "invalid-target"},
        )

    assert len(witness_chain.entries) == before_count
    assert (
        witness_chain.current_state_hash
        == before_hash
    )


def test_wrong_amount_does_not_change_witness_history():
    witness_chain, escrow, ledger, money = (
        build_locked_escrow()
    )

    before_count = len(witness_chain.entries)
    before_state = witness_chain.current_state.copy()

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-V80-008",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=999999,
            timestamp="2026-09-03T13:08:00Z",
            evidence={"type": "wrong-amount"},
        )

    assert len(witness_chain.entries) == before_count
    assert (
        witness_chain.current_state
        == before_state
    )


def test_success_after_failure_creates_clean_witness_history():
    witness_chain, escrow, ledger, money = (
        build_locked_escrow()
    )

    before_count = len(witness_chain.entries)

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-V80-009",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=2000000,
            timestamp="2026-09-03T13:09:00Z",
            evidence={"type": "failed"},
        )

    assert len(witness_chain.entries) == before_count

    money.atomic_settlement(
        transaction_id="SUCCESS-V80-009",
        target_state="RELEASED",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T13:10:00Z",
        evidence={"type": "delivery-confirmed"},
    )

    assert (
        len(witness_chain.entries)
        == before_count + 2
    )

    assert (
        witness_chain.entries[-2]
        .record.event_type
        == "ATOMIC_SETTLEMENT"
    )

    assert (
        witness_chain.entries[-1]
        .record.event_type
        == "ESCROW_TRANSITION"
    )

    assert (
        escrow.get_state()["state"]
        == "RELEASED"
    )
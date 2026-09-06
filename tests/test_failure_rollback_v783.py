import copy

import pytest

from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from witness.chain import WitnessChain


@pytest.fixture
def settlement():
    witness_chain = WitnessChain(
        initial_state={
            "initialized": False,
            "sequence_counter": 0,
        },
        manifest={
            "project": "V78.3-Failure-Rollback-Audit",
            "version": "0",
        },
        witness_id="witness-rollback-01",
    )

    escrow = EscrowEngine(
        escrow_id="ESC-783",
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

    return {
        "witness": witness_chain,
        "escrow": escrow,
        "ledger": ledger,
        "money": money,
    }


def fund_and_lock(settlement):
    money = settlement["money"]
    escrow = settlement["escrow"]

    money.transfer(
        transaction_id="DEP-783",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T08:00:00Z",
        evidence={"type": "deposit"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T08:00:01Z",
        {"type": "funded"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T08:00:02Z",
        {"type": "locked"},
    )


def test_failure_does_not_change_balances(settlement):
    fund_and_lock(settlement)

    money = settlement["money"]
    ledger = settlement["ledger"]

    old_balances = copy.deepcopy(ledger.balances)

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-001",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=2000000,
            timestamp="2026-09-03T08:01:00Z",
            evidence={"type": "forced-failure"},
        )

    assert ledger.balances == old_balances


def test_failure_does_not_change_escrow_state(settlement):
    fund_and_lock(settlement)

    money = settlement["money"]
    escrow = settlement["escrow"]

    old_state = escrow.get_state()

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-002",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=2000000,
            timestamp="2026-09-03T08:02:00Z",
            evidence={"type": "forced-failure"},
        )

    assert escrow.get_state() == old_state


def test_failure_does_not_create_money_record(settlement):
    fund_and_lock(settlement)

    money = settlement["money"]

    old_count = len(money.records)

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-003",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=2000000,
            timestamp="2026-09-03T08:03:00Z",
            evidence={"type": "forced-failure"},
        )

    assert len(money.records) == old_count


def test_invalid_target_preserves_everything(settlement):
    fund_and_lock(settlement)

    money = settlement["money"]
    escrow = settlement["escrow"]
    ledger = settlement["ledger"]

    old_state = escrow.get_state()
    old_balances = copy.deepcopy(ledger.balances)
    old_records = len(money.records)

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-004",
            target_state="CANCELLED",
            source="ESCROW",
            destination="SELLER",
            amount=1000000,
            timestamp="2026-09-03T08:04:00Z",
            evidence={"type": "invalid-target"},
        )

    assert escrow.get_state() == old_state
    assert ledger.balances == old_balances
    assert len(money.records) == old_records


def test_wrong_amount_preserves_everything(settlement):
    fund_and_lock(settlement)

    money = settlement["money"]
    escrow = settlement["escrow"]
    ledger = settlement["ledger"]

    old_state = escrow.get_state()
    old_balances = copy.deepcopy(ledger.balances)

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-005",
            target_state="REFUNDED",
            source="ESCROW",
            destination="BUYER",
            amount=500000,
            timestamp="2026-09-03T08:05:00Z",
            evidence={"type": "wrong-amount"},
        )

    assert escrow.get_state() == old_state
    assert ledger.balances == old_balances


def test_non_locked_escrow_preserves_money(settlement):
    money = settlement["money"]
    ledger = settlement["ledger"]
    escrow = settlement["escrow"]

    money.transfer(
        transaction_id="DEP-784",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T08:06:00Z",
        evidence={"type": "deposit"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T08:06:01Z",
        {"type": "funded"},
    )

    old_balances = copy.deepcopy(ledger.balances)
    old_state = escrow.get_state()

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-006",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=1000000,
            timestamp="2026-09-03T08:06:02Z",
            evidence={"type": "not-locked"},
        )

    assert ledger.balances == old_balances
    assert escrow.get_state() == old_state


def test_success_after_previous_failure_still_works(settlement):
    fund_and_lock(settlement)

    money = settlement["money"]
    ledger = settlement["ledger"]
    escrow = settlement["escrow"]

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-007",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=2000000,
            timestamp="2026-09-03T08:07:00Z",
            evidence={"type": "forced-failure"},
        )

    record = money.atomic_settlement(
        transaction_id="SUCCESS-007",
        target_state="RELEASED",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T08:07:01Z",
        evidence={"type": "valid-release"},
    )

    assert record.amount == 1000000
    assert ledger.get_balance("ESCROW") == 0
    assert ledger.get_balance("SELLER") == 1000000
    assert escrow.get_state()["state"] == "RELEASED"


def test_total_money_is_preserved_after_failure(
    settlement,
):
    fund_and_lock(settlement)

    money = settlement["money"]
    ledger = settlement["ledger"]

    total_before = sum(ledger.balances.values())

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="FAIL-008",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=9999999,
            timestamp="2026-09-03T08:08:00Z",
            evidence={"type": "overflow"},
        )

    total_after = sum(ledger.balances.values())

    assert total_before == total_after
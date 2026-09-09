import copy

import pytest

from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from witness.chain import WitnessChain


def build_locked_escrow():
    witness = WitnessChain(
        initial_state={
            "test": "initial",
        },
        manifest={
            "test": "manifest",
        },
        witness_id="TEST-WITNESS",
    )
    ledger = MoneyLedger(currency="MNT")
    ledger.create_account("seller", 1_000_000)
    ledger.create_account("escrow-001", 0)
    ledger.create_account("buyer", 0)

    escrow = EscrowEngine(
        escrow_id="escrow-001",
        amount=1_000_000,
        currency="MNT",
        witness_chain=witness,
    )

    money = MoneyEngine(
        ledger=ledger,
        escrow=escrow,
    )

    money.transfer(
        source="seller",
        destination="escrow-001",
        amount=1_000_000,
        transaction_id="FUND-001",
        timestamp="2026-01-01T00:00:00Z",
        evidence={"test": "fund"},
    )

    escrow.transition(
        "FUNDED",
        "2026-01-01T00:00:01Z",
        {"test": "funded"},
    )

    escrow.transition(
        "LOCKED",
        "2026-01-01T00:00:02Z",
        {"test": "locked"},
    )

    return witness, ledger, escrow, money


def test_failure_after_witness_append_rolls_back_everything():
    witness, ledger, escrow, money = build_locked_escrow()

    witness_entries_before = copy.deepcopy(witness.entries)
    witness_state_before = copy.deepcopy(witness.current_state)
    witness_hash_before = witness.current_state_hash
    balances_before = copy.deepcopy(ledger.balances)
    escrow_state_before = copy.deepcopy(escrow.state)
    records_before = copy.deepcopy(money.records)

    original_transition = escrow.transition

    def forced_failure(*args, **kwargs):
        raise RuntimeError("FORCED POST-WITNESS FAILURE")

    escrow.transition = forced_failure

    with pytest.raises(RuntimeError, match="FORCED POST-WITNESS FAILURE"):
        money.atomic_settlement(
            source="escrow-001",
            destination="buyer",
            amount=1_000_000,
            target_state="RELEASED",
            transaction_id="SETTLE-FAIL-001",
            timestamp="2026-01-01T00:00:03Z",
            evidence={"test": "forced-failure"},
        )

    escrow.transition = original_transition

    assert witness.entries == witness_entries_before
    assert witness.current_state == witness_state_before
    assert witness.current_state_hash == witness_hash_before
    assert ledger.balances == balances_before
    assert escrow.state == escrow_state_before
    assert money.records == records_before


def test_success_after_post_witness_failure_is_clean():
    witness, ledger, escrow, money = build_locked_escrow()

    original_transition = escrow.transition

    def forced_failure(*args, **kwargs):
        raise RuntimeError("FORCED POST-WITNESS FAILURE")

    escrow.transition = forced_failure

    with pytest.raises(RuntimeError, match="FORCED POST-WITNESS FAILURE"):
        money.atomic_settlement(
            source="escrow-001",
            destination="buyer",
            amount=1_000_000,
            target_state="RELEASED",
            transaction_id="SETTLE-FAIL-002",
            timestamp="2026-01-01T00:00:03Z",
            evidence={"test": "forced-failure"},
        )

    escrow.transition = original_transition

    witness_count_before_success = len(witness.entries)

    money.atomic_settlement(
        source="escrow-001",
        destination="buyer",
        amount=1_000_000,
        target_state="RELEASED",
        transaction_id="SETTLE-SUCCESS-001",
        timestamp="2026-01-01T00:00:04Z",
        evidence={"test": "success"},
    )

    assert len(witness.entries) == witness_count_before_success + 2
    assert witness.entries[-2].record.event_type == "ATOMIC_SETTLEMENT"
    assert witness.entries[-1].record.event_type == "ESCROW_TRANSITION"
    assert escrow.state["state"] == "RELEASED"
    assert ledger.get_balance("escrow-001") == 0
    assert ledger.get_balance("buyer") == 1_000_000

def test_transfer_failure_after_witness_append_rolls_back_everything():
    witness = WitnessChain(
        initial_state={
            "test": "initial",
        },
        manifest={
            "test": "manifest",
        },
        witness_id="TEST-WITNESS-TRANSFER",
    )

    ledger = MoneyLedger(currency="MNT")
    ledger.create_account("seller", 1_000_000)
    ledger.create_account("buyer", 0)

    escrow = EscrowEngine(
        escrow_id="escrow-transfer",
        amount=1_000_000,
        currency="MNT",
        witness_chain=witness,
    )

    money = MoneyEngine(
        ledger=ledger,
        escrow=escrow,
    )

    witness_entries_before = copy.deepcopy(witness.entries)
    witness_state_before = copy.deepcopy(witness.current_state)
    witness_hash_before = witness.current_state_hash
    balances_before = copy.deepcopy(ledger.balances)
    records_before = copy.deepcopy(money.records)

    original_transfer = ledger.transfer

    def forced_failure(*args, **kwargs):
        raise RuntimeError("FORCED TRANSFER FAILURE")

    ledger.transfer = forced_failure

    with pytest.raises(
        RuntimeError,
        match="FORCED TRANSFER FAILURE",
    ):
        money.transfer(
            source="seller",
            destination="buyer",
            amount=500_000,
            transaction_id="TRANSFER-FAIL-001",
            timestamp="2026-01-01T00:00:00Z",
            evidence={"test": "forced-transfer-failure"},
        )

    ledger.transfer = original_transfer

    assert witness.entries == witness_entries_before
    assert witness.current_state == witness_state_before
    assert witness.current_state_hash == witness_hash_before
    assert ledger.balances == balances_before
    assert money.records == records_before

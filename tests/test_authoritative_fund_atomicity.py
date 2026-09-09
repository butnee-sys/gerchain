import copy

import pytest

from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from services.authoritative_escrow import AuthoritativeEscrowService
from witness.chain import WitnessChain


def build_service():
    witness = WitnessChain(
        initial_state={
            "test": "initial",
        },
        manifest={
            "test": "authoritative-fund",
        },
        witness_id="AUTH-FUND-WITNESS",
    )

    ledger = MoneyLedger(currency="MNT")
    ledger.create_account("buyer", 1_000_000)
    ledger.create_account("escrow-001", 0)

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

    verifier = None

    service = AuthoritativeEscrowService(
        escrow_engine=escrow,
        money_engine=money,
        verifier=verifier,
    )

    return service, witness, ledger, escrow, money


def test_fund_failure_after_money_transfer_rolls_back_everything():
    service, witness, ledger, escrow, money = build_service()

    witness_entries_before = copy.deepcopy(witness.entries)
    witness_state_before = copy.deepcopy(witness.current_state)
    witness_hash_before = witness.current_state_hash
    balances_before = copy.deepcopy(ledger.balances)
    escrow_state_before = copy.deepcopy(escrow.state)
    records_before = copy.deepcopy(money.records)

    original_transition = escrow.transition

    def forced_failure(*args, **kwargs):
        raise RuntimeError("FORCED FUNDED TRANSITION FAILURE")

    escrow.transition = forced_failure

    with pytest.raises(
        RuntimeError,
        match="FORCED FUNDED TRANSITION FAILURE",
    ):
        service.fund(
            transaction_id="FUND-AUTH-FAIL-001",
            source="buyer",
            timestamp="2026-01-01T00:00:00Z",
            evidence={"test": "forced-failure"},
        )

    escrow.transition = original_transition

    assert ledger.balances == balances_before
    assert escrow.state == escrow_state_before
    assert money.records == records_before
    assert witness.entries == witness_entries_before
    assert witness.current_state == witness_state_before
    assert witness.current_state_hash == witness_hash_before


def test_fund_succeeds_after_failure():
    service, witness, ledger, escrow, money = build_service()

    original_transition = escrow.transition

    def forced_failure(*args, **kwargs):
        raise RuntimeError("FORCED FUNDED TRANSITION FAILURE")

    escrow.transition = forced_failure

    with pytest.raises(
        RuntimeError,
        match="FORCED FUNDED TRANSITION FAILURE",
    ):
        service.fund(
            transaction_id="FUND-AUTH-FAIL-002",
            source="buyer",
            timestamp="2026-01-01T00:00:00Z",
            evidence={"test": "forced-failure"},
        )

    escrow.transition = original_transition

    result = service.fund(
        transaction_id="FUND-AUTH-SUCCESS-001",
        source="buyer",
        timestamp="2026-01-01T00:00:01Z",
        evidence={"test": "success"},
    )

    assert result.state == "FUNDED"
    assert ledger.get_balance("buyer") == 0
    assert ledger.get_balance("escrow-001") == 1_000_000
    assert escrow.state["state"] == "FUNDED"
    assert len(money.records) == 1
    assert len(witness.entries) == 2

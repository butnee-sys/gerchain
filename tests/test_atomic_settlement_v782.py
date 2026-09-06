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
            "project": "V78.2-Atomic-Settlement",
            "version": "0",
        },
        witness_id="witness-settlement-01",
    )

    escrow = EscrowEngine(
        escrow_id="ESC-782",
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
        "witness_chain": witness_chain,
        "escrow": escrow,
        "ledger": ledger,
        "money": money,
    }


def fund_and_lock(settlement):
    escrow = settlement["escrow"]
    money = settlement["money"]

    money.transfer(
        transaction_id="DEP-001",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T07:00:00Z",
        evidence={"type": "deposit"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T07:00:01Z",
        {"type": "funded"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T07:00:02Z",
        {"type": "locked"},
    )


def test_atomic_release_moves_money_and_changes_state(
    settlement,
):
    fund_and_lock(settlement)

    money = settlement["money"]
    ledger = settlement["ledger"]
    escrow = settlement["escrow"]

    record = money.atomic_settlement(
        transaction_id="SET-RELEASE-001",
        target_state="RELEASED",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T07:10:00Z",
        evidence={"type": "delivery-confirmed"},
    )

    assert record.amount == 1000000
    assert ledger.get_balance("ESCROW") == 0
    assert ledger.get_balance("SELLER") == 1000000
    assert escrow.get_state()["state"] == "RELEASED"


def test_atomic_refund_moves_money_and_changes_state(
    settlement,
):
    fund_and_lock(settlement)

    money = settlement["money"]
    ledger = settlement["ledger"]
    escrow = settlement["escrow"]

    record = money.atomic_settlement(
        transaction_id="SET-REFUND-001",
        target_state="REFUNDED",
        source="ESCROW",
        destination="BUYER",
        amount=1000000,
        timestamp="2026-09-03T07:11:00Z",
        evidence={"type": "refund-approved"},
    )

    assert record.amount == 1000000
    assert ledger.get_balance("ESCROW") == 0
    assert ledger.get_balance("BUYER") == 2000000
    assert escrow.get_state()["state"] == "REFUNDED"


def test_atomic_release_is_witnessed(settlement):
    fund_and_lock(settlement)

    money = settlement["money"]
    witness_chain = settlement["witness_chain"]

    before = len(witness_chain.entries)

    money.atomic_settlement(
        transaction_id="SET-WITNESS-001",
        target_state="RELEASED",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T07:12:00Z",
        evidence={"type": "delivery"},
    )

    assert len(witness_chain.entries) == before + 2

    records = [
        entry.record
        for entry in witness_chain.entries
    ]

    assert records[-1].event_type == "ESCROW_TRANSITION"


def test_atomic_settlement_requires_locked(
    settlement,
):
    money = settlement["money"]

    money.transfer(
        transaction_id="DEP-002",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T07:13:00Z",
        evidence={"type": "deposit"},
    )

    settlement["escrow"].transition(
        "FUNDED",
        "2026-09-03T07:13:01Z",
        {"type": "funded"},
    )

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="SET-INVALID-001",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=1000000,
            timestamp="2026-09-03T07:13:02Z",
            evidence={"type": "invalid"},
        )


def test_atomic_settlement_amount_must_match_escrow(
    settlement,
):
    fund_and_lock(settlement)

    money = settlement["money"]

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="SET-INVALID-002",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=500000,
            timestamp="2026-09-03T07:14:00Z",
            evidence={"type": "wrong-amount"},
        )


def test_atomic_settlement_preserves_total_money(
    settlement,
):
    fund_and_lock(settlement)

    money = settlement["money"]
    ledger = settlement["ledger"]

    total_before = sum(
        ledger.balances.values()
    )

    money.atomic_settlement(
        transaction_id="SET-INVARIANT-001",
        target_state="RELEASED",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T07:15:00Z",
        evidence={"type": "delivery"},
    )

    total_after = sum(
        ledger.balances.values()
    )

    assert total_before == total_after


def test_atomic_settlement_failure_preserves_escrow_state(
    settlement,
):
    fund_and_lock(settlement)

    money = settlement["money"]
    ledger = settlement["ledger"]
    escrow = settlement["escrow"]

    old_state = escrow.get_state()
    old_balances = dict(ledger.balances)

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="SET-FAIL-001",
            target_state="RELEASED",
            source="ESCROW",
            destination="SELLER",
            amount=2000000,
            timestamp="2026-09-03T07:16:00Z",
            evidence={"type": "failure"},
        )

    assert escrow.get_state() == old_state
    assert ledger.balances == old_balances


def test_atomic_settlement_rejects_invalid_target(
    settlement,
):
    fund_and_lock(settlement)

    money = settlement["money"]

    with pytest.raises(ValueError):
        money.atomic_settlement(
            transaction_id="SET-INVALID-003",
            target_state="CANCELLED",
            source="ESCROW",
            destination="SELLER",
            amount=1000000,
            timestamp="2026-09-03T07:17:00Z",
            evidence={"type": "invalid-target"},
        )


def test_atomic_release_record_is_cryptographically_bound(
    settlement,
):
    fund_and_lock(settlement)

    money = settlement["money"]

    record = money.atomic_settlement(
        transaction_id="SET-HASH-001",
        target_state="RELEASED",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T07:18:00Z",
        evidence={"type": "delivery"},
    )

    assert len(record.transfer_hash) == 64
    assert len(record.witness_event_hash) == 64
    assert record.witness_id == "witness-settlement-01"
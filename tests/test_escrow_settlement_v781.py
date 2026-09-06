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
            "project": "V78.1-Settlement",
            "version": "0",
        },
        witness_id="witness-settlement-01",
    )

    escrow = EscrowEngine(
        escrow_id="ESC-SET-001",
        amount=1000000,
        currency="MNT",
        witness_chain=witness_chain,
    )

    ledger = MoneyLedger("MNT")

    ledger.create_account(
        "BUYER",
        2000000,
    )

    ledger.create_account(
        "ESCROW",
        0,
    )

    ledger.create_account(
        "SELLER",
        0,
    )

    money = MoneyEngine(
        ledger=ledger,
        escrow=escrow,
    )

    return escrow, money


def test_deposit_then_lock(settlement):
    escrow, money = settlement

    money.transfer(
        transaction_id="DEP-001",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T08:00:00Z",
        evidence={"doc": "deposit-001"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T08:01:00Z",
        {"doc": "funded-001"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T08:02:00Z",
        {"doc": "locked-001"},
    )

    assert money.ledger.get_balance("BUYER") == 1000000
    assert money.ledger.get_balance("ESCROW") == 1000000
    assert escrow.get_state()["state"] == "LOCKED"


def test_locked_release_to_seller(settlement):
    escrow, money = settlement

    money.transfer(
        transaction_id="DEP-002",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T08:10:00Z",
        evidence={"doc": "deposit-002"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T08:11:00Z",
        {"doc": "funded-002"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T08:12:00Z",
        {"doc": "locked-002"},
    )

    money.transfer(
        transaction_id="REL-002",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T08:13:00Z",
        evidence={"doc": "release-002"},
    )

    escrow.transition(
        "RELEASED",
        "2026-09-03T08:14:00Z",
        {"doc": "released-002"},
    )

    assert money.ledger.get_balance("BUYER") == 1000000
    assert money.ledger.get_balance("ESCROW") == 0
    assert money.ledger.get_balance("SELLER") == 1000000
    assert escrow.get_state()["state"] == "RELEASED"


def test_locked_refund_to_buyer(settlement):
    escrow, money = settlement

    money.transfer(
        transaction_id="DEP-003",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T08:20:00Z",
        evidence={"doc": "deposit-003"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T08:21:00Z",
        {"doc": "funded-003"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T08:22:00Z",
        {"doc": "locked-003"},
    )

    money.transfer(
        transaction_id="REF-003",
        source="ESCROW",
        destination="BUYER",
        amount=1000000,
        timestamp="2026-09-03T08:23:00Z",
        evidence={"doc": "refund-003"},
    )

    escrow.transition(
        "REFUNDED",
        "2026-09-03T08:24:00Z",
        {"doc": "refunded-003"},
    )

    assert money.ledger.get_balance("BUYER") == 2000000
    assert money.ledger.get_balance("ESCROW") == 0
    assert money.ledger.get_balance("SELLER") == 0
    assert escrow.get_state()["state"] == "REFUNDED"


def test_release_without_lock_is_rejected(settlement):
    escrow, money = settlement

    money.transfer(
        transaction_id="DEP-004",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T08:30:00Z",
        evidence={"doc": "deposit-004"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T08:31:00Z",
        {"doc": "funded-004"},
    )

    with pytest.raises(ValueError):
        escrow.transition(
            "RELEASED",
            "2026-09-03T08:32:00Z",
            {"doc": "invalid-release-004"},
        )


def test_refund_without_lock_is_rejected(settlement):
    escrow, money = settlement

    money.transfer(
        transaction_id="DEP-005",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T08:40:00Z",
        evidence={"doc": "deposit-005"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T08:41:00Z",
        {"doc": "funded-005"},
    )

    with pytest.raises(ValueError):
        escrow.transition(
            "REFUNDED",
            "2026-09-03T08:42:00Z",
            {"doc": "invalid-refund-005"},
        )


def test_cannot_release_more_than_escrow_balance(settlement):
    escrow, money = settlement

    money.transfer(
        transaction_id="DEP-006",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T08:50:00Z",
        evidence={"doc": "deposit-006"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T08:51:00Z",
        {"doc": "funded-006"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T08:52:00Z",
        {"doc": "locked-006"},
    )

    with pytest.raises(ValueError):
        money.transfer(
            transaction_id="REL-006",
            source="ESCROW",
            destination="SELLER",
            amount=1000001,
            timestamp="2026-09-03T08:53:00Z",
            evidence={"doc": "invalid-release-006"},
        )


def test_full_release_path_is_witnessed(settlement):
    escrow, money = settlement

    money.transfer(
        transaction_id="DEP-007",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T09:00:00Z",
        evidence={"doc": "deposit-007"},
    )

    escrow.transition(
        "FUNDED",
        "2026-09-03T09:01:00Z",
        {"doc": "funded-007"},
    )

    escrow.transition(
        "LOCKED",
        "2026-09-03T09:02:00Z",
        {"doc": "locked-007"},
    )

    money.transfer(
        transaction_id="REL-007",
        source="ESCROW",
        destination="SELLER",
        amount=1000000,
        timestamp="2026-09-03T09:03:00Z",
        evidence={"doc": "release-007"},
    )

    escrow.transition(
        "RELEASED",
        "2026-09-03T09:04:00Z",
        {"doc": "released-007"},
    )

    witness_entries = escrow.witness_chain.entries

    assert len(witness_entries) == 5

    event_types = [
        entry.record.event_type
        for entry in witness_entries
    ]

    assert event_types == [
        "MONEY_TRANSFER",
        "ESCROW_TRANSITION",
        "ESCROW_TRANSITION",
        "MONEY_TRANSFER",
        "ESCROW_TRANSITION",
    ]
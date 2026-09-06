import pytest

from core.hashing import domain_hash
from escrow.engine import EscrowEngine
from money.engine import MoneyEngine
from money.ledger import MoneyLedger
from witness.chain import WitnessChain


@pytest.fixture
def money_engine():
    witness_chain = WitnessChain(
        initial_state={
            "initialized": False,
            "sequence_counter": 0,
        },
        manifest={
            "project": "V78-Money",
            "version": "0",
        },
        witness_id="witness-money-01",
    )

    escrow = EscrowEngine(
        escrow_id="ESC-MONEY-001",
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

    return MoneyEngine(
        ledger=ledger,
        escrow=escrow,
    )


def test_initial_balances(money_engine):
    assert money_engine.ledger.get_balance("BUYER") == 2000000
    assert money_engine.ledger.get_balance("ESCROW") == 0
    assert money_engine.ledger.get_balance("SELLER") == 0


def test_money_transfer(money_engine):
    record = money_engine.transfer(
        transaction_id="TX-001",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T07:00:00Z",
        evidence={"doc": "deposit-001"},
    )

    assert record.amount == 1000000
    assert record.currency == "MNT"

    assert money_engine.ledger.get_balance("BUYER") == 1000000
    assert money_engine.ledger.get_balance("ESCROW") == 1000000


def test_transfer_record_hash(money_engine):
    record = money_engine.transfer(
        transaction_id="TX-002",
        source="BUYER",
        destination="ESCROW",
        amount=500000,
        timestamp="2026-09-03T07:01:00Z",
        evidence={"doc": "deposit-002"},
    )

    expected = domain_hash(
        "MONEY_TRANSFER",
        {
            "transaction_id": "TX-002",
            "sequence": 1,
            "source": "BUYER",
            "destination": "ESCROW",
            "amount": 500000,
            "currency": "MNT",
            "previous_source_balance": 2000000,
            "new_source_balance": 1500000,
            "previous_destination_balance": 0,
            "new_destination_balance": 500000,
        },
    )

    assert record.transfer_hash == expected
    assert len(record.transfer_hash) == 64


def test_insufficient_balance_rejected(money_engine):
    with pytest.raises(ValueError):
        money_engine.transfer(
            transaction_id="TX-003",
            source="BUYER",
            destination="ESCROW",
            amount=3000000,
            timestamp="2026-09-03T07:02:00Z",
            evidence={"doc": "invalid-001"},
        )


def test_witness_receives_money_event(money_engine):
    money_engine.transfer(
        transaction_id="TX-004",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T07:03:00Z",
        evidence={"doc": "deposit-004"},
    )

    assert len(
        money_engine.escrow.witness_chain.entries
    ) == 1

    witness_record = (
        money_engine
        .escrow
        .witness_chain
        .entries[0]
        .record
    )

    assert witness_record.event_type == "MONEY_TRANSFER"
    assert witness_record.event_id == "MONEY-TX-004-1"
    assert witness_record.witness_id == "witness-money-01"


def test_multiple_transfers(money_engine):
    money_engine.transfer(
        transaction_id="TX-005",
        source="BUYER",
        destination="ESCROW",
        amount=1000000,
        timestamp="2026-09-03T07:04:00Z",
        evidence={"doc": "deposit-005"},
    )

    money_engine.transfer(
        transaction_id="TX-006",
        source="ESCROW",
        destination="SELLER",
        amount=400000,
        timestamp="2026-09-03T07:05:00Z",
        evidence={"doc": "release-005"},
    )

    assert money_engine.ledger.get_balance("BUYER") == 1000000
    assert money_engine.ledger.get_balance("ESCROW") == 600000
    assert money_engine.ledger.get_balance("SELLER") == 400000


def test_money_records_are_sequenced(money_engine):
    first = money_engine.transfer(
        transaction_id="TX-007",
        source="BUYER",
        destination="ESCROW",
        amount=700000,
        timestamp="2026-09-03T07:06:00Z",
        evidence={"doc": "deposit-007"},
    )

    second = money_engine.transfer(
        transaction_id="TX-008",
        source="ESCROW",
        destination="SELLER",
        amount=300000,
        timestamp="2026-09-03T07:07:00Z",
        evidence={"doc": "release-007"},
    )

    assert first.sequence == 1
    assert second.sequence == 2


def test_negative_amount_rejected(money_engine):
    with pytest.raises(ValueError):
        money_engine.transfer(
            transaction_id="TX-009",
            source="BUYER",
            destination="ESCROW",
            amount=-100,
            timestamp="2026-09-03T07:08:00Z",
            evidence={"doc": "invalid-002"},
        )
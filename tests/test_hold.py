import pytest

from core.hold import HoldConflictError, HoldEngine, HoldState


def test_hold_reserves_without_moving_balance():
    engine = HoldEngine()
    hold = engine.create(
        hold_id="H-001",
        account_id="A-001",
        amount=300,
        currency="MNT",
        available_balance=1_000,
    )

    assert hold.state == HoldState.ACTIVE
    assert engine.reserved("A-001") == 300
    assert engine.available("A-001", 1_000) == 700


def test_hold_fails_when_available_balance_is_insufficient():
    engine = HoldEngine()

    with pytest.raises(HoldConflictError):
        engine.create(
            hold_id="H-002",
            account_id="A-001",
            amount=1_001,
            currency="MNT",
            available_balance=1_000,
        )


def test_same_hold_id_cannot_be_created_twice():
    engine = HoldEngine()
    engine.create(
        hold_id="H-003",
        account_id="A-001",
        amount=100,
        currency="MNT",
        available_balance=1_000,
    )

    with pytest.raises(HoldConflictError):
        engine.create(
            hold_id="H-003",
            account_id="A-001",
            amount=100,
            currency="MNT",
            available_balance=1_000,
        )


def test_releasing_hold_returns_amount_to_available_capacity():
    engine = HoldEngine()
    engine.create(
        hold_id="H-004",
        account_id="A-001",
        amount=400,
        currency="MNT",
        available_balance=1_000,
    )

    engine.release("H-004")

    assert engine.reserved("A-001") == 0
    assert engine.available("A-001", 1_000) == 1_000

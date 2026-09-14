import pytest

from core.transaction_lifecycle import (
    InvalidTransitionError,
    TransactionState,
    TransactionStateMachine,
)


def test_happy_path_reaches_finality():
    machine = TransactionStateMachine()

    for state in (
        TransactionState.PENDING,
        TransactionState.ACTIVE,
        TransactionState.LOCKED,
        TransactionState.PROCESSING,
        TransactionState.COMPLETED,
        TransactionState.FINAL,
    ):
        machine.transition(state)

    assert machine.state == TransactionState.FINAL


def test_invalid_transition_fails_closed():
    machine = TransactionStateMachine(TransactionState.CREATED)

    with pytest.raises(InvalidTransitionError):
        machine.transition(TransactionState.FINAL)


def test_final_state_is_terminal():
    machine = TransactionStateMachine(TransactionState.FINAL)

    assert not machine.can_transition(TransactionState.CREATED)

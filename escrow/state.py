"""
GerChain V77.0
Escrow state machine.

Purpose:
- Deterministic escrow lifecycle.
- Every transition has an explicit previous and next state.
- Invalid state transitions are rejected.
"""

from __future__ import annotations

from typing import Any, Dict


ESCROW_STATES = {
    "CREATED",
    "FUNDED",
    "LOCKED",
    "RELEASED",
    "REFUNDED",
    "CANCELLED",
}


ALLOWED_TRANSITIONS = {
    "CREATED": {"FUNDED", "CANCELLED"},
    "FUNDED": {"LOCKED", "CANCELLED"},
    "LOCKED": {"RELEASED", "REFUNDED"},
    "RELEASED": set(),
    "REFUNDED": set(),
    "CANCELLED": set(),
}


def validate_escrow_state(state: str) -> None:
    """Эскроу төлөв хүчинтэй эсэхийг шалгана."""

    if state not in ESCROW_STATES:
        raise ValueError(
            f"Invalid escrow state: {state}"
        )


def apply_escrow_transition(
    escrow: Dict[str, Any],
    target_state: str,
) -> Dict[str, Any]:
    """
    Эскроу төлөвийг детерминистик байдлаар шилжүүлнэ.

    Зөвшөөрөгдсөн төлөвийн шилжилтээс бусад бүх шилжилтийг
    татгалзана.
    """

    current_state = escrow.get("state")

    validate_escrow_state(current_state)
    validate_escrow_state(target_state)

    allowed = ALLOWED_TRANSITIONS[current_state]

    if target_state not in allowed:
        raise ValueError(
            f"Invalid escrow transition: "
            f"{current_state} -> {target_state}"
        )

    new_escrow = dict(escrow)

    new_escrow["previous_state"] = current_state
    new_escrow["state"] = target_state

    transition_counter = new_escrow.get(
        "transition_counter",
        0,
    )

    new_escrow["transition_counter"] = (
        transition_counter + 1
    )

    return new_escrow


__all__ = [
    "ESCROW_STATES",
    "ALLOWED_TRANSITIONS",
    "validate_escrow_state",
    "apply_escrow_transition",
]
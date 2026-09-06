"""
GerChain V76.0
Deterministic state transition engine.
"""

import copy
from typing import Dict, Any


def apply_transition(
    state: Dict[str, Any],
    event: Dict[str, Any],
) -> Dict[str, Any]:
    """Детерминистик төлөвийн шилжилт тооцоологч."""
    new_state = copy.deepcopy(state)

    payload = event.get("payload", {})

    if "value" in payload:
        new_state["value"] = payload["value"]

    new_state["sequence_counter"] = event.get(
        "sequence",
        new_state.get("sequence_counter", 0) + 1,
    )

    new_state["initialized"] = True

    return new_state


__all__ = [
    "apply_transition",
]
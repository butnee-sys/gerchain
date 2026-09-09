"""
GerChain V77.0
Escrow Engine.

Purpose:
- Deterministic escrow lifecycle.
- Every state transition is cryptographically recorded.
- Invalid transitions are rejected.
"""

from __future__ import annotations

import copy
from typing import Any, Dict

from core.hashing import domain_hash
from escrow.record import EscrowRecord
from escrow.state import apply_escrow_transition
from witness.chain import WitnessChain


class EscrowEngine:
    """WitnessChain дээр суурилсан эскроу хөдөлгүүр."""

    def __init__(
        self,
        escrow_id: str,
        amount: int,
        currency: str,
        witness_chain: WitnessChain,
    ):
        if amount < 0:
            raise ValueError("Escrow amount cannot be negative.")

        self.escrow_id = escrow_id
        self.amount = amount
        self.currency = currency
        self.witness_chain = witness_chain

        self.state: Dict[str, Any] = {
            "escrow_id": escrow_id,
            "state": "CREATED",
            "amount": amount,
            "currency": currency,
            "transition_counter": 0,
        }

        self.records = []

    def transition(
        self,
        target_state: str,
        timestamp: str,
        evidence: Any,
    ) -> EscrowRecord:

        previous_state = self.state["state"]

        new_state = apply_escrow_transition(
            self.state,
            target_state,
        )

        transition_obj = {
            "escrow_id": self.escrow_id,
            "sequence": new_state["transition_counter"],
            "previous_state": previous_state,
            "new_state": target_state,
            "amount": self.amount,
            "currency": self.currency,
        }

        transition_hash = domain_hash(
            "ESCROW_TRANSITION",
            transition_obj,
        )

        witness_record = self.witness_chain.append_event(
            event_id=(
                f"{self.escrow_id}-"
                f"{new_state['transition_counter']}"
            ),
            event_type="ESCROW_TRANSITION",
            timestamp=timestamp,
            payload=transition_obj,
            evidence=evidence,
        )

        record = EscrowRecord(
            escrow_id=self.escrow_id,
            sequence=new_state["transition_counter"],
            previous_state=previous_state,
            new_state=target_state,
            amount=self.amount,
            currency=self.currency,
            transition_hash=transition_hash,
            witness_event_hash=witness_record.event_hash,
            witness_id=witness_record.witness_id,
        )

        self.records.append(record)
        self.state = copy.deepcopy(new_state)

        return record

    def get_state(self) -> Dict[str, Any]:
        """Одоогийн эскроу төлөвийг буцаана."""

        return copy.deepcopy(self.state)


__all__ = [
    "EscrowEngine",
]
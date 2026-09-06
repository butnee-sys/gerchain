import copy
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from core.hashing import domain_hash
from core.state import apply_transition
from witness.record import WitnessRecord


@dataclass
class ChainEntry:
    record: WitnessRecord
    event_payload: Dict[str, Any]
    evidence: Any


class WitnessChain:
    def __init__(
        self,
        initial_state: Dict[str, Any],
        manifest: Dict[str, Any],
        witness_id: str,
        initial_money_state: Optional[Dict[str, Any]] = None,
    ):
        self.initial_state = copy.deepcopy(
            initial_state
        )

        self.manifest = copy.deepcopy(
            manifest
        )

        self.manifest_hash = domain_hash(
            "MANIFEST",
            self.manifest,
        )

        self.witness_id = witness_id

        # V80.4.2:
        # Initial Money State Commitment
        self.initial_money_state = (
            copy.deepcopy(initial_money_state)
            if initial_money_state is not None
            else None
        )

        if self.initial_money_state is not None:
            self.initial_money_state_hash = (
                domain_hash(
                    "INITIAL_MONEY_STATE",
                    self.initial_money_state,
                )
            )
        else:
            self.initial_money_state_hash = None

        self.entries: List[ChainEntry] = []

        self.current_state = copy.deepcopy(
            initial_state
        )

        self.current_state_hash = domain_hash(
            "STATE",
            self.current_state,
        )

    def get_initial_money_commitment(
        self,
    ) -> Optional[Dict[str, Any]]:
        """
        V80.4.2:

        Эхний мөнгөний төлөв болон түүний
        криптографийн commitment-ийг буцаана.
        """

        if self.initial_money_state is None:
            return None

        return {
            "state": copy.deepcopy(
                self.initial_money_state
            ),
            "state_hash": (
                self.initial_money_state_hash
            ),
        }

    def verify_initial_money_commitment(
        self,
    ) -> bool:
        """
        V80.4.2:

        Хадгалсан эхний мөнгөний төлөвийн
        hash-ийг дахин тооцож шалгана.
        """

        if self.initial_money_state is None:
            return False

        if self.initial_money_state_hash is None:
            return False

        recalculated_hash = domain_hash(
            "INITIAL_MONEY_STATE",
            self.initial_money_state,
        )

        return (
            recalculated_hash
            == self.initial_money_state_hash
        )

    def append_event(
        self,
        event_id: str,
        event_type: str,
        timestamp: str,
        payload: Dict[str, Any],
        evidence: Any,
    ) -> WitnessRecord:

        sequence = len(self.entries) + 1

        event_obj = {
            "sequence": sequence,
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": timestamp,
            "payload": payload,
        }

        event_hash = domain_hash(
            "WITNESS_EVENT",
            event_obj,
        )

        evidence_hash = domain_hash(
            "EVIDENCE",
            evidence,
        )

        new_state = apply_transition(
            self.current_state,
            event_obj,
        )

        new_state_hash = domain_hash(
            "STATE",
            new_state,
        )

        record = WitnessRecord(
            sequence=sequence,
            event_id=event_id,
            event_type=event_type,
            timestamp=timestamp,
            previous_state_hash=(
                self.current_state_hash
            ),
            event_hash=event_hash,
            new_state_hash=new_state_hash,
            evidence_hash=evidence_hash,
            witness_id=self.witness_id,
            manifest_hash=self.manifest_hash,
        )

        self.entries.append(
            ChainEntry(
                record,
                copy.deepcopy(payload),
                copy.deepcopy(evidence),
            )
        )

        self.current_state = new_state
        self.current_state_hash = new_state_hash

        return record
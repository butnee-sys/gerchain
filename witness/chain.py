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

    def _checkpoint(self) -> Dict[str, Any]:
        """
        Internal transactional checkpoint.

        Used to restore witness history when a higher-level
        atomic operation fails after witness append.
        """
        return {
            "entries": copy.deepcopy(self.entries),
            "current_state": copy.deepcopy(self.current_state),
            "current_state_hash": self.current_state_hash,
        }

    def _restore(self, checkpoint: Dict[str, Any]) -> None:
        """
        Internal rollback of witness state to a checkpoint.
        """
        self.entries = copy.deepcopy(
            checkpoint["entries"]
        )
        self.current_state = copy.deepcopy(
            checkpoint["current_state"]
        )
        self.current_state_hash = checkpoint[
            "current_state_hash"
        ]

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

    @classmethod
    def from_dict(
        cls,
        bundle: Dict[str, Any],
    ) -> "WitnessChain":
        """
        Reconstruct a WitnessChain from a serialized bundle.

        Recovery is verification-first:
        - never calls append_event()
        - never trusts stored hashes
        - reconstructs and verifies every event/state transition
        - preserves the exact stored WitnessRecord values
        - recovers the authoritative initial money state from
          the INITIAL_MONEY_STATE event
        """

        if not isinstance(bundle, dict):
            raise ValueError("Witness bundle must be a dictionary")

        required_keys = {
            "manifest",
            "manifest_hash",
            "witness_id",
            "initial_state",
            "entries",
        }
        missing = required_keys - set(bundle.keys())
        if missing:
            raise ValueError(
                f"Witness bundle missing required fields: {sorted(missing)}"
            )

        manifest = bundle["manifest"]
        manifest_hash = bundle["manifest_hash"]
        witness_id = bundle["witness_id"]
        initial_state = bundle["initial_state"]
        raw_entries = bundle["entries"]

        if not isinstance(manifest, dict):
            raise ValueError("Witness manifest must be a dictionary")

        if not isinstance(manifest_hash, str):
            raise ValueError("Witness manifest_hash must be a string")

        if not isinstance(witness_id, str) or not witness_id:
            raise ValueError("Witness witness_id must be a non-empty string")

        if not isinstance(initial_state, dict):
            raise ValueError("Witness initial_state must be a dictionary")

        if not isinstance(raw_entries, list):
            raise ValueError("Witness entries must be a list")

        recalculated_manifest_hash = domain_hash(
            "MANIFEST",
            manifest,
        )
        if recalculated_manifest_hash != manifest_hash:
            raise ValueError(
                "Witness manifest hash mismatch during recovery"
            )

        recovered_initial_money_state = None
        recovered_initial_money_state_hash = None
        recovered_entries: List[ChainEntry] = []

        current_state = copy.deepcopy(initial_state)
        current_state_hash = domain_hash(
            "STATE",
            current_state,
        )

        for expected_sequence, raw_entry in enumerate(
            raw_entries,
            start=1,
        ):
            if not isinstance(raw_entry, dict):
                raise ValueError(
                    f"Witness entry {expected_sequence} must be a dictionary"
                )

            if set(raw_entry.keys()) != {
                "record",
                "event_payload",
                "evidence",
            }:
                raise ValueError(
                    f"Witness entry {expected_sequence} has invalid fields"
                )

            raw_record = raw_entry["record"]
            event_payload = raw_entry["event_payload"]
            evidence = raw_entry["evidence"]

            if not isinstance(raw_record, dict):
                raise ValueError(
                    f"Witness record {expected_sequence} must be a dictionary"
                )

            record_fields = {
                "sequence",
                "event_id",
                "event_type",
                "timestamp",
                "previous_state_hash",
                "event_hash",
                "new_state_hash",
                "evidence_hash",
                "witness_id",
                "manifest_hash",
            }

            if set(raw_record.keys()) != record_fields:
                raise ValueError(
                    f"Witness record {expected_sequence} has invalid fields"
                )

            sequence = raw_record["sequence"]
            event_id = raw_record["event_id"]
            event_type = raw_record["event_type"]
            timestamp = raw_record["timestamp"]
            previous_state_hash = raw_record["previous_state_hash"]
            stored_event_hash = raw_record["event_hash"]
            stored_new_state_hash = raw_record["new_state_hash"]
            stored_evidence_hash = raw_record["evidence_hash"]
            stored_witness_id = raw_record["witness_id"]
            stored_manifest_hash = raw_record["manifest_hash"]

            if (
                not isinstance(sequence, int)
                or isinstance(sequence, bool)
                or sequence != expected_sequence
            ):
                raise ValueError(
                    f"Witness sequence mismatch at entry {expected_sequence}"
                )

            if not isinstance(event_id, str) or not event_id:
                raise ValueError(
                    f"Witness event_id invalid at sequence {sequence}"
                )

            if not isinstance(event_type, str) or not event_type:
                raise ValueError(
                    f"Witness event_type invalid at sequence {sequence}"
                )

            if not isinstance(timestamp, str):
                raise ValueError(
                    f"Witness timestamp invalid at sequence {sequence}"
                )

            hash_fields = {
                "previous_state_hash": previous_state_hash,
                "event_hash": stored_event_hash,
                "new_state_hash": stored_new_state_hash,
                "evidence_hash": stored_evidence_hash,
                "witness_id": stored_witness_id,
                "manifest_hash": stored_manifest_hash,
            }

            if not all(
                isinstance(value, str)
                for value in hash_fields.values()
            ):
                raise ValueError(
                    f"Witness record hashes/identifiers invalid at sequence {sequence}"
                )

            if stored_witness_id != witness_id:
                raise ValueError(
                    f"Witness ID mismatch at sequence {sequence}"
                )

            if stored_manifest_hash != manifest_hash:
                raise ValueError(
                    f"Witness manifest hash mismatch at sequence {sequence}"
                )

            if previous_state_hash != current_state_hash:
                raise ValueError(
                    f"Witness previous state hash mismatch at sequence {sequence}"
                )

            event_obj = {
                "sequence": sequence,
                "event_id": event_id,
                "event_type": event_type,
                "timestamp": timestamp,
                "payload": event_payload,
            }

            recalculated_event_hash = domain_hash(
                "WITNESS_EVENT",
                event_obj,
            )
            if recalculated_event_hash != stored_event_hash:
                raise ValueError(
                    f"Witness event hash mismatch at sequence {sequence}"
                )

            recalculated_evidence_hash = domain_hash(
                "EVIDENCE",
                evidence,
            )
            if recalculated_evidence_hash != stored_evidence_hash:
                raise ValueError(
                    f"Witness evidence hash mismatch at sequence {sequence}"
                )

            new_state = apply_transition(
                current_state,
                event_obj,
            )
            recalculated_new_state_hash = domain_hash(
                "STATE",
                new_state,
            )
            if recalculated_new_state_hash != stored_new_state_hash:
                raise ValueError(
                    f"Witness new state hash mismatch at sequence {sequence}"
                )

            if event_type == "INITIAL_MONEY_STATE":
                if recovered_initial_money_state is not None:
                    raise ValueError(
                        "Multiple INITIAL_MONEY_STATE events are not allowed"
                    )

                if not isinstance(event_payload, dict):
                    raise ValueError(
                        "INITIAL_MONEY_STATE payload must be a dictionary"
                    )

                if set(event_payload.keys()) != {
                    "state",
                    "state_hash",
                }:
                    raise ValueError(
                        "INITIAL_MONEY_STATE payload has invalid fields"
                    )

                money_state = event_payload["state"]
                money_state_hash = event_payload["state_hash"]

                if not isinstance(money_state, dict):
                    raise ValueError(
                        "INITIAL_MONEY_STATE state must be a dictionary"
                    )

                if not isinstance(money_state_hash, str):
                    raise ValueError(
                        "INITIAL_MONEY_STATE state_hash must be a string"
                    )

                recalculated_money_hash = domain_hash(
                    "INITIAL_MONEY_STATE",
                    money_state,
                )
                if recalculated_money_hash != money_state_hash:
                    raise ValueError(
                        "INITIAL_MONEY_STATE commitment mismatch during recovery"
                    )

                recovered_initial_money_state = copy.deepcopy(
                    money_state
                )
                recovered_initial_money_state_hash = money_state_hash

            recovered_entries.append(
                ChainEntry(
                    WitnessRecord(
                        sequence=sequence,
                        event_id=event_id,
                        event_type=event_type,
                        timestamp=timestamp,
                        previous_state_hash=previous_state_hash,
                        event_hash=stored_event_hash,
                        new_state_hash=stored_new_state_hash,
                        evidence_hash=stored_evidence_hash,
                        witness_id=stored_witness_id,
                        manifest_hash=stored_manifest_hash,
                    ),
                    copy.deepcopy(event_payload),
                    copy.deepcopy(evidence),
                )
            )

            current_state = new_state
            current_state_hash = recalculated_new_state_hash

        recovered = cls(
            initial_state=initial_state,
            manifest=manifest,
            witness_id=witness_id,
            initial_money_state=recovered_initial_money_state,
        )

        if (
            recovered_initial_money_state is not None
            and recovered.initial_money_state_hash
            != recovered_initial_money_state_hash
        ):
            raise ValueError(
                "Recovered initial money commitment mismatch"
            )

        recovered.entries = recovered_entries
        recovered.current_state = copy.deepcopy(current_state)
        recovered.current_state_hash = current_state_hash

        return recovered

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
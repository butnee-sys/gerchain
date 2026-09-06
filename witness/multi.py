"""
GerChain V79.1.1
Validated Multi-Witness Consensus Engine.

Purpose:
- Олон гэрчийн бүртгэлийг зөвшилцөлд оруулахаас
  өмнө эх өгөгдөлтэй нь тулгаж шалгах.
- event_hash, evidence_hash, state_hash,
  manifest_hash-ийг дахин тооцоолох.
- Танихгүй гэрч болон өөрчилсөн бүртгэлийг хасах.
- Зөвхөн хүчинтэй гэрчүүдийн саналаар зөвшилцөл тогтоох.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from core.hashing import domain_hash
from core.state import apply_transition
from witness.chain import WitnessChain
from witness.record import WitnessRecord


@dataclass(frozen=True)
class ConsensusResult:
    """Олон гэрчийн зөвшилцлийн үр дүн."""

    status: str
    consensus_hash: Optional[str]
    votes: int
    quorum: int
    dissenting_witness_ids: List[str]


class MultiWitnessEngine:
    """Криптографийн баталгаажуулалттай олон гэрчийн хөдөлгүүр."""

    def __init__(
        self,
        witnesses: List[WitnessChain],
        quorum: int,
    ):
        if not witnesses:
            raise ValueError(
                "At least one witness is required."
            )

        witness_ids = [
            witness.witness_id
            for witness in witnesses
        ]

        if len(set(witness_ids)) != len(witness_ids):
            raise ValueError(
                "Duplicate witness IDs are not allowed."
            )

        if quorum < 2:
            raise ValueError(
                "Quorum must be at least 2."
            )

        if quorum > len(witnesses):
            raise ValueError(
                "Quorum cannot exceed witness count."
            )

        self.witnesses = list(witnesses)
        self.quorum = quorum

        self.witness_map: Dict[str, WitnessChain] = {
            witness.witness_id: witness
            for witness in witnesses
        }

    def _get_chain_entry(
        self,
        record: WitnessRecord,
    ):
        """Гэрчийн эх бүртгэлийг өөрийн chain-ээс олно."""

        chain = self.witness_map.get(
            record.witness_id
        )

        if chain is None:
            return None

        for entry in chain.entries:
            if entry.record.sequence == record.sequence:
                return entry

        return None

    def _validate_record(
        self,
        record: WitnessRecord,
    ) -> bool:
        """Бүртгэлийг эх өгөгдөлтэй нь тулгаж криптографаар шалгана."""

        chain = self.witness_map.get(
            record.witness_id
        )

        if chain is None:
            return False

        entry = self._get_chain_entry(record)

        if entry is None:
            return False

        original = entry.record

        if record.event_id != original.event_id:
            return False

        if record.event_type != original.event_type:
            return False

        if record.timestamp != original.timestamp:
            return False

        if record.sequence != original.sequence:
            return False

        if record.witness_id != original.witness_id:
            return False

        if record.manifest_hash != chain.manifest_hash:
            return False

        if record.manifest_hash != original.manifest_hash:
            return False

        expected_event_hash = domain_hash(
            "WITNESS_EVENT",
            {
                "sequence": record.sequence,
                "event_id": record.event_id,
                "event_type": record.event_type,
                "timestamp": record.timestamp,
                "payload": entry.event_payload,
            },
        )

        if record.event_hash != expected_event_hash:
            return False

        expected_evidence_hash = domain_hash(
            "EVIDENCE",
            entry.evidence,
        )

        if record.evidence_hash != expected_evidence_hash:
            return False

        expected_initial_state = chain.initial_state

        if record.sequence == 1:
            expected_previous_state_hash = domain_hash(
                "STATE",
                expected_initial_state,
            )
        else:
            previous_entry = None

            for candidate in chain.entries:
                if candidate.record.sequence == (
                    record.sequence - 1
                ):
                    previous_entry = candidate
                    break

            if previous_entry is None:
                return False

            expected_previous_state_hash = (
                previous_entry.record.new_state_hash
            )

        if (
            record.previous_state_hash
            != expected_previous_state_hash
        ):
            return False

        recomputed_state = (
            expected_initial_state.copy()
        )

        for candidate in chain.entries:
            if candidate.record.sequence > record.sequence:
                break

            event_obj = {
                "sequence": candidate.record.sequence,
                "event_id": candidate.record.event_id,
                "event_type": candidate.record.event_type,
                "timestamp": candidate.record.timestamp,
                "payload": candidate.event_payload,
            }

            recomputed_state = apply_transition(
                recomputed_state,
                event_obj,
            )

        expected_new_state_hash = domain_hash(
            "STATE",
            recomputed_state,
        )

        if (
            record.new_state_hash
            != expected_new_state_hash
        ):
            return False

        return True

    def evaluate(
        self,
        records: List[WitnessRecord],
    ) -> ConsensusResult:
        """Бүх гэрчийг шалгаад зөвшилцөл тогтооно."""

        if len(records) != len(self.witnesses):
            raise ValueError(
                "Record count must equal witness count."
            )

        valid_records = []
        invalid_witness_ids = []

        for record in records:
            if self._validate_record(record):
                valid_records.append(record)
            else:
                invalid_witness_ids.append(
                    record.witness_id
                )

        hash_votes: Dict[str, List[str]] = {}

        for record in valid_records:
            if record.event_hash not in hash_votes:
                hash_votes[record.event_hash] = []

            hash_votes[
                record.event_hash
            ].append(record.witness_id)

        winning_hash = None
        winning_witness_ids: List[str] = []

        for event_hash, witness_ids in hash_votes.items():
            if len(witness_ids) > len(
                winning_witness_ids
            ):
                winning_hash = event_hash
                winning_witness_ids = witness_ids

        votes = len(winning_witness_ids)

        if votes >= self.quorum:
            status = "CONSENSUS"
        else:
            status = "REJECTED"

        dissenting_witness_ids = [
            record.witness_id
            for record in records
            if record.witness_id
            not in winning_witness_ids
        ]

        for witness_id in invalid_witness_ids:
            if witness_id not in dissenting_witness_ids:
                dissenting_witness_ids.append(
                    witness_id
                )

        return ConsensusResult(
            status=status,
            consensus_hash=(
                winning_hash
                if status == "CONSENSUS"
                else None
            ),
            votes=votes,
            quorum=self.quorum,
            dissenting_witness_ids=(
                dissenting_witness_ids
            ),
        )


__all__ = [
    "ConsensusResult",
    "MultiWitnessEngine",
]
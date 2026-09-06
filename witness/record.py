from dataclasses import dataclass


@dataclass(frozen=True)
class WitnessRecord:
    """Өөрчлөгдөшгүй (Immutable) гэрчийн бүртгэлийн нэгж."""

    sequence: int
    event_id: str
    event_type: str
    timestamp: str
    previous_state_hash: str
    event_hash: str
    new_state_hash: str
    evidence_hash: str
    witness_id: str
    manifest_hash: str
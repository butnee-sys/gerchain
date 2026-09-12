from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from uuid import UUID, uuid4


@dataclass(frozen=True)
class EvidenceEvent:
    event_id: UUID
    incident_id: UUID
    event_type: str
    occurred_at: datetime
    payload_hash: str

    @classmethod
    def create(cls, incident_id: UUID, event_type: str, canonical_payload: str) -> "EvidenceEvent":
        digest = sha256(canonical_payload.encode("utf-8")).hexdigest()
        return cls(
            event_id=uuid4(),
            incident_id=incident_id,
            event_type=event_type,
            occurred_at=datetime.now(timezone.utc),
            payload_hash=digest,
        )

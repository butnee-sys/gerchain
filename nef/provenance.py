from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ProvenanceRecord:
    provenance_id: str
    asset_id: str
    source_type: str
    source_id: str
    action: str
    actor_id: str
    previous_provenance_id: str | None = None
    created_at: datetime = field(default_factory=utc_now)


class EvidenceProvenanceEngine:
    def create(
        self,
        provenance_id: str,
        asset_id: str,
        source_type: str,
        source_id: str,
        action: str,
        actor_id: str,
        previous_provenance_id: str | None = None,
    ) -> ProvenanceRecord:
        required = {
            "provenance_id": provenance_id,
            "asset_id": asset_id,
            "source_type": source_type,
            "source_id": source_id,
            "action": action,
            "actor_id": actor_id,
        }

        for name, value in required.items():
            if not value:
                raise ValueError(f"{name} is required")

        return ProvenanceRecord(
            provenance_id=provenance_id,
            asset_id=asset_id,
            source_type=source_type,
            source_id=source_id,
            action=action,
            actor_id=actor_id,
            previous_provenance_id=previous_provenance_id,
        )

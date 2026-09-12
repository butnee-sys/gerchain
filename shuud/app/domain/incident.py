from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4
from datetime import datetime, timezone


class IncidentType(StrEnum):
    MINOR_COLLISION = "MINOR_COLLISION"
    BREAKDOWN = "BREAKDOWN"
    OBSTACLE = "OBSTACLE"
    ROAD_BLOCKAGE = "ROAD_BLOCKAGE"
    OTHER = "OTHER"


class IncidentState(StrEnum):
    REPORTED = "REPORTED"
    VERIFIED = "VERIFIED"
    DISPATCHED = "DISPATCHED"
    ON_SCENE = "ON_SCENE"
    CLEARING = "CLEARING"
    CLEARED = "CLEARED"
    CLAIM_OPENED = "CLAIM_OPENED"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"


_ALLOWED: dict[IncidentState, frozenset[IncidentState]] = {
    IncidentState.REPORTED: frozenset({IncidentState.VERIFIED, IncidentState.ESCALATED}),
    IncidentState.VERIFIED: frozenset({IncidentState.DISPATCHED, IncidentState.ESCALATED}),
    IncidentState.DISPATCHED: frozenset({IncidentState.ON_SCENE, IncidentState.ESCALATED}),
    IncidentState.ON_SCENE: frozenset({IncidentState.CLEARING, IncidentState.ESCALATED}),
    IncidentState.CLEARING: frozenset({IncidentState.CLEARED, IncidentState.ESCALATED}),
    IncidentState.CLEARED: frozenset({IncidentState.CLAIM_OPENED, IncidentState.CLOSED}),
    IncidentState.CLAIM_OPENED: frozenset({IncidentState.CLOSED}),
    IncidentState.CLOSED: frozenset(),
    IncidentState.ESCALATED: frozenset(),
}


@dataclass(frozen=True)
class Incident:
    incident_id: UUID
    incident_type: IncidentType
    latitude: float
    longitude: float
    reported_at: datetime
    state: IncidentState = IncidentState.REPORTED

    @classmethod
    def create(
        cls,
        incident_type: IncidentType,
        latitude: float,
        longitude: float,
    ) -> "Incident":
        return cls(
            incident_id=uuid4(),
            incident_type=incident_type,
            latitude=latitude,
            longitude=longitude,
            reported_at=datetime.now(timezone.utc),
        )

    def transition(self, target: IncidentState) -> "Incident":
        if target not in _ALLOWED[self.state]:
            raise ValueError(f"invalid incident transition: {self.state} -> {target}")
        return Incident(
            incident_id=self.incident_id,
            incident_type=self.incident_type,
            latitude=self.latitude,
            longitude=self.longitude,
            reported_at=self.reported_at,
            state=target,
        )

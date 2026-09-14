"""SHUUD incident domain model.

This is intentionally an application/domain model. Cryptographic evidence,
verification and settlement remain GerChain responsibilities.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4


@dataclass(frozen=True)
class Incident:
    incident_id: str
    occurred_at: datetime
    location: str
    vehicle_a: Optional[str] = None
    vehicle_b: Optional[str] = None
    description: Optional[str] = None


def create_incident(
    location: str,
    *,
    vehicle_a: Optional[str] = None,
    vehicle_b: Optional[str] = None,
    description: Optional[str] = None,
    occurred_at: Optional[datetime] = None,
) -> Incident:
    """Create a canonical SHUUD incident record.

    No decision is made here. The incident must pass through evidence and
    verification before SHIID can authorize a downstream state transition.
    """
    if not location or not location.strip():
        raise ValueError("location is required")

    timestamp = occurred_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise ValueError("occurred_at must be timezone-aware")

    return Incident(
        incident_id=f"INC-{uuid4().hex[:12].upper()}",
        occurred_at=timestamp,
        location=location.strip(),
        vehicle_a=vehicle_a.strip() if vehicle_a else None,
        vehicle_b=vehicle_b.strip() if vehicle_b else None,
        description=description.strip() if description else None,
    )


__all__ = ["Incident", "create_incident"]

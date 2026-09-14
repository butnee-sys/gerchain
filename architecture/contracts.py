"""Small, dependency-free contracts for the frozen DEE architecture.

These contracts define boundaries only. They do not implement ledger, escrow,
release, settlement, or asset truth; those remain owned by the existing core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class ActorType(str, Enum):
    STATE = "state"
    COMPANY = "company"
    PERSON = "person"


@dataclass(frozen=True)
class BoundaryRequest:
    actor_type: ActorType
    actor_id: str
    activity: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    credential: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class BoundaryResponse:
    accepted: bool
    activity: str
    correlation_id: str | None = None
    data: Mapping[str, Any] = field(default_factory=dict)
    reason: str | None = None


class BoundaryError(RuntimeError):
    """Raised when a boundary contract is violated."""


class AdapterContract:
    """Marker contract for explicit architecture adapters."""

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        raise NotImplementedError


__all__ = [
    "ActorType",
    "BoundaryRequest",
    "BoundaryResponse",
    "BoundaryError",
    "AdapterContract",
]

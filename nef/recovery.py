from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RecoveryStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class RecoveryRequest:
    recovery_id: str
    asset_id: str
    target_version: int
    requested_by: str
    reason: str
    status: RecoveryStatus = RecoveryStatus.REQUESTED
    snapshot: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)


class NEFRecoveryEngine:
    def request(
        self,
        recovery_id: str,
        asset_id: str,
        target_version: int,
        requested_by: str,
        reason: str,
        snapshot: dict[str, Any] | None = None,
    ) -> RecoveryRequest:
        if not recovery_id:
            raise ValueError("recovery_id is required")
        if not asset_id:
            raise ValueError("asset_id is required")
        if target_version < 1:
            raise ValueError("target_version must be >= 1")
        if not requested_by:
            raise ValueError("requested_by is required")
        if not reason:
            raise ValueError("reason is required")

        return RecoveryRequest(
            recovery_id=recovery_id,
            asset_id=asset_id,
            target_version=target_version,
            requested_by=requested_by,
            reason=reason,
            snapshot=dict(snapshot or {}),
        )

    def approve(self, request: RecoveryRequest) -> RecoveryRequest:
        if request.status != RecoveryStatus.REQUESTED:
            raise ValueError("only REQUESTED recovery can be approved")

        return RecoveryRequest(
            recovery_id=request.recovery_id,
            asset_id=request.asset_id,
            target_version=request.target_version,
            requested_by=request.requested_by,
            reason=request.reason,
            status=RecoveryStatus.APPROVED,
            snapshot=dict(request.snapshot),
            created_at=request.created_at,
        )

    def complete(self, request: RecoveryRequest) -> RecoveryRequest:
        if request.status != RecoveryStatus.APPROVED:
            raise ValueError("only APPROVED recovery can be completed")

        return RecoveryRequest(
            recovery_id=request.recovery_id,
            asset_id=request.asset_id,
            target_version=request.target_version,
            requested_by=request.requested_by,
            reason=request.reason,
            status=RecoveryStatus.COMPLETED,
            snapshot=dict(request.snapshot),
            created_at=request.created_at,
        )

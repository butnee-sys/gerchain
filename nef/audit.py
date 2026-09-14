from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class AuditRecord:
    audit_id: str
    asset_id: str
    action: str
    actor_id: str
    result: str
    details: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)


class NEFAuditEngine:
    def record(
        self,
        audit_id: str,
        asset_id: str,
        action: str,
        actor_id: str,
        result: str,
        details: dict[str, Any] | None = None,
    ) -> AuditRecord:
        required = {
            "audit_id": audit_id,
            "asset_id": asset_id,
            "action": action,
            "actor_id": actor_id,
            "result": result,
        }

        for name, value in required.items():
            if not value:
                raise ValueError(f"{name} is required")

        return AuditRecord(
            audit_id=audit_id,
            asset_id=asset_id,
            action=action,
            actor_id=actor_id,
            result=result,
            details=dict(details or {}),
        )

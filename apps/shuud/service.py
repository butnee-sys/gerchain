from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from architecture.contracts import BoundaryRequest, BoundaryResponse


@dataclass(frozen=True)
class SHUUDDecision:
    approved: bool
    compensation: int
    reason: str


class SHUUDService:
    """SHUUD application service; it orchestrates, but does not own core truth."""

    ACTIVITY = "shuud-rapid-release"

    def __init__(self, release_handler: Any | None = None) -> None:
        self.release_handler = release_handler

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        payload: Mapping[str, Any] = request.payload
        required = ("incident_id", "vehicle_id", "compensation", "evidence_verified")
        missing = [key for key in required if key not in payload]
        if missing:
            return BoundaryResponse(False, request.activity, request.correlation_id, reason=f"Missing fields: {', '.join(missing)}")

        compensation = int(payload["compensation"])
        if compensation <= 0 or compensation > 2_000_000:
            return BoundaryResponse(False, request.activity, request.correlation_id, reason="Compensation limit exceeded")
        if payload["evidence_verified"] is not True:
            return BoundaryResponse(False, request.activity, request.correlation_id, reason="Evidence not verified")

        decision = SHUUDDecision(True, compensation, "rapid-release eligible")
        if self.release_handler is None:
            return BoundaryResponse(True, request.activity, request.correlation_id, {
                "incident_id": payload["incident_id"],
                "vehicle_id": payload["vehicle_id"],
                "compensation": decision.compensation,
                "status": "RELEASE_READY",
            })

        result = self.release_handler(payload)
        return BoundaryResponse(True, request.activity, request.correlation_id, {
            "incident_id": payload["incident_id"],
            "vehicle_id": payload["vehicle_id"],
            "compensation": decision.compensation,
            "status": "RELEASE_SUBMITTED",
            "release": result,
        })


__all__ = ["SHUUDDecision", "SHUUDService"]

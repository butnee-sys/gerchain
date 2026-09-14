from __future__ import annotations

from typing import Any

from architecture.contracts import BoundaryRequest, BoundaryResponse


class EXIMGateway:
    """Controlled two-way boundary between I2B services and governed core.

    EXIM validates the boundary request and routes it onward; it does not own
    ledger, escrow, authorization, settlement, or asset truth.
    """

    def __init__(self, downstream: Any | None = None) -> None:
        self.downstream = downstream

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        if not request.correlation_id:
            return BoundaryResponse(False, request.activity, reason="Correlation ID is required")
        if not request.actor_id:
            return BoundaryResponse(False, request.activity, request.correlation_id, reason="Actor ID is required")
        if self.downstream is None:
            return BoundaryResponse(False, request.activity, request.correlation_id, reason="EXIM downstream is not configured")
        response = self.downstream.handle(request)
        if not isinstance(response, BoundaryResponse):
            return BoundaryResponse(False, request.activity, request.correlation_id, reason="Invalid downstream boundary response")
        return response


__all__ = ["EXIMGateway"]

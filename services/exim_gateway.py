from __future__ import annotations

from typing import Any

from architecture.contracts import BoundaryRequest, BoundaryResponse
from architecture.ports import EXIMToI2BAdapter


class EXIMGateway:
    """Controlled EXIM boundary; routing occurs through an explicit adapter."""

    def __init__(self, downstream: Any | None = None, *, adapter: EXIMToI2BAdapter | None = None) -> None:
        self.downstream = downstream
        self.adapter = adapter

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        if not request.correlation_id:
            return BoundaryResponse(False, request.activity, reason="Correlation ID is required")
        if not request.actor_id:
            return BoundaryResponse(False, request.activity, request.correlation_id, reason="Actor ID is required")
        if self.adapter is None:
            return BoundaryResponse(False, request.activity, request.correlation_id, reason="EXIM-to-I2B adapter is not configured")
        if self.downstream is None:
            return BoundaryResponse(False, request.activity, request.correlation_id, reason="EXIM downstream is not configured")
        response = self.adapter.handle(request) if hasattr(self.adapter, "handle") else None
        if response is None:
            return BoundaryResponse(False, request.activity, request.correlation_id, reason="EXIM adapter rejected request")
        if not isinstance(response, BoundaryResponse):
            return BoundaryResponse(False, request.activity, request.correlation_id, reason="Invalid adapter response")
        return response


__all__ = ["EXIMGateway"]

from __future__ import annotations

from architecture.contracts import BoundaryRequest, BoundaryResponse
from architecture.governed_flow_adapters import DEEToG3BoundaryAdapter, G3ToCoreBoundaryAdapter
from apps.shuud.integration.shuud_exim_flow import SHUUDEximFlow


class SHUUDGovernedFlow:
    """SHUUD application composition root through frozen platform boundaries."""

    def __init__(self, *, i2b_exim: SHUUDEximFlow, dee_to_g3: DEEToG3BoundaryAdapter, g3_to_core: G3ToCoreBoundaryAdapter) -> None:
        self._i2b_exim = i2b_exim
        self._dee_to_g3 = dee_to_g3
        self._g3_to_core = g3_to_core

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        response = self._i2b_exim.handle(request)
        if not response.accepted:
            return response
        response = self._dee_to_g3.handle(response_to_request(request, response))
        if not response.accepted:
            return response
        return self._g3_to_core.handle(response_to_request(request, response))


def response_to_request(request: BoundaryRequest, response: BoundaryResponse) -> BoundaryRequest:
    payload = dict(request.payload)
    payload.update(dict(response.data or {}))
    return BoundaryRequest(
        actor_type=request.actor_type,
        actor_id=request.actor_id,
        activity=request.activity,
        payload=payload,
        credential=request.credential,
        correlation_id=request.correlation_id,
    )


__all__ = ["SHUUDGovernedFlow"]

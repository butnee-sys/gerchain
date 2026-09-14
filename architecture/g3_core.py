"""G-3 to Core boundary adapter.

This module is intentionally a thin boundary adapter. It carries G-3 policy
context and NEF asset references into an injected Core boundary without
importing or re-implementing GerChain engines.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .contracts import AdapterContract, BoundaryError, BoundaryRequest, BoundaryResponse


CoreHandler = Callable[[BoundaryRequest], BoundaryResponse]


class G3ToCoreBoundaryAdapter(AdapterContract):
    """Route governed G-3 requests to an existing Core boundary.

    The handler is injected by the composition root. This keeps the adapter
    independent from GerChain's internal package layout and prevents a second
    operational engine from appearing at the architecture boundary.
    """

    REQUIRED_ASSET_FIELDS = ("asset_id",)
    REQUIRED_G3_FIELDS = ("condition_policy",)
    REQUIRED_ESCROW_FIELDS = ("escrow",)

    def __init__(self, core_handler: CoreHandler):
        if not callable(core_handler):
            raise TypeError("core_handler must be callable")
        self._core_handler = core_handler

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        if not isinstance(request, BoundaryRequest):
            raise BoundaryError("G-3/Core adapter requires BoundaryRequest")
        if not request.activity:
            raise BoundaryError("activity is required")

        payload: Mapping[str, Any] = request.payload
        self._require_mapping(payload, "asset")
        self._require_mapping(payload, "condition_policy")
        self._require_mapping(payload, "escrow")

        asset = payload["asset"]
        if not isinstance(asset, Mapping):
            raise BoundaryError("asset must be a mapping")
        for field in self.REQUIRED_ASSET_FIELDS:
            if not asset.get(field):
                raise BoundaryError(f"asset.{field} is required")

        # G-3 is the policy owner; Core remains authoritative for operational
        # decision, authorization, escrow, release, settlement and value flow.
        forwarded = BoundaryRequest(
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            activity=request.activity,
            payload=dict(payload),
            credential=request.credential,
            correlation_id=request.correlation_id,
        )
        response = self._core_handler(forwarded)
        if not isinstance(response, BoundaryResponse):
            raise BoundaryError("Core handler must return BoundaryResponse")
        return response

    @staticmethod
    def _require_mapping(payload: Mapping[str, Any], key: str) -> None:
        if key not in payload:
            raise BoundaryError(f"G-3/Core payload requires '{key}'")
        if not isinstance(payload[key], Mapping):
            raise BoundaryError(f"G-3/Core payload '{key}' must be a mapping")


__all__ = ["G3ToCoreBoundaryAdapter", "CoreHandler"]

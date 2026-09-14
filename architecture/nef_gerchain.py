"""Explicit NEF -> GerChain boundary contract.

NEF owns authoritative asset truth. GerChain owns authoritative value flow.
This adapter carries a verified NEF asset reference into the existing
G-3/Core boundary without implementing ledger, escrow, release or settlement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .contracts import AdapterContract, BoundaryError, BoundaryRequest, BoundaryResponse


@dataclass(frozen=True)
class NEFAssetReference:
    asset_id: str
    valuation_id: str
    verification_id: str
    validation_status: str
    asset_version: int
    value: int
    currency: str = "MNT"

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "NEFAssetReference":
        required = (
            "asset_id",
            "valuation_id",
            "verification_id",
            "validation_status",
            "asset_version",
            "value",
        )
        missing = [key for key in required if key not in payload]
        if missing:
            raise BoundaryError(f"NEF asset reference missing: {', '.join(missing)}")
        if payload["validation_status"] != "VALID":
            raise BoundaryError("NEF asset must be VALID before value flow")
        if not isinstance(payload["asset_version"], int) or payload["asset_version"] < 1:
            raise BoundaryError("NEF asset_version must be a positive integer")
        if not isinstance(payload["value"], int) or isinstance(payload["value"], bool) or payload["value"] <= 0:
            raise BoundaryError("NEF asset value must be a positive integer")
        if not all(str(payload[key]).strip() for key in ("asset_id", "valuation_id", "verification_id")):
            raise BoundaryError("NEF asset identity references are required")
        return cls(
            asset_id=str(payload["asset_id"]),
            valuation_id=str(payload["valuation_id"]),
            verification_id=str(payload["verification_id"]),
            validation_status=str(payload["validation_status"]),
            asset_version=int(payload["asset_version"]),
            value=int(payload["value"]),
            currency=str(payload.get("currency", "MNT")),
        )


class NEFToGerChainAdapter(AdapterContract):
    """Validate NEF truth and forward only an explicit asset reference."""

    def __init__(self, downstream: AdapterContract):
        if not isinstance(downstream, AdapterContract):
            raise TypeError("downstream must implement AdapterContract")
        self._downstream = downstream

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        if not isinstance(request, BoundaryRequest):
            raise BoundaryError("NEF/GerChain adapter requires BoundaryRequest")
        asset = request.payload.get("asset")
        if not isinstance(asset, Mapping):
            raise BoundaryError("NEF/GerChain request requires asset mapping")
        reference = NEFAssetReference.from_payload(asset)
        forwarded_payload = dict(request.payload)
        forwarded_payload["asset"] = {
            "asset_id": reference.asset_id,
            "valuation_id": reference.valuation_id,
            "verification_id": reference.verification_id,
            "validation_status": reference.validation_status,
            "asset_version": reference.asset_version,
            "value": reference.value,
            "currency": reference.currency,
        }
        forwarded = BoundaryRequest(
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            activity=request.activity,
            payload=forwarded_payload,
            credential=request.credential,
            correlation_id=request.correlation_id,
        )
        return self._downstream.handle(forwarded)


__all__ = ["NEFAssetReference", "NEFToGerChainAdapter"]

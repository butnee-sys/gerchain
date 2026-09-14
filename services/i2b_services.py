from __future__ import annotations

from typing import Any, Mapping

from architecture.contracts import BoundaryRequest, BoundaryResponse
from services.i2b_service_center import ServiceCenter


def _require(payload: Mapping[str, Any], *keys: str) -> None:
    missing = [key for key in keys if not payload.get(key)]
    if missing:
        raise ValueError(f"missing service fields: {', '.join(missing)}")


def register_core_services(center: ServiceCenter, *, nef: Any | None = None, gerchain: Any | None = None) -> None:
    """Register thin I2B services; authoritative state remains in NEF/GerChain."""

    def asset_information(request: BoundaryRequest) -> Mapping[str, Any]:
        _require(request.payload, "asset_id")
        if nef is None:
            return {"asset_id": request.payload["asset_id"], "status": "SERVICE_BOUNDARY_READY"}
        handler = getattr(nef, "get_asset", None) or getattr(nef, "get", None)
        if handler is None:
            return {"asset_id": request.payload["asset_id"], "status": "SERVICE_BOUNDARY_READY"}
        return {"asset": handler(request.payload["asset_id"])}

    def account_balance(request: BoundaryRequest) -> Mapping[str, Any]:
        _require(request.payload, "account_id")
        if gerchain is None:
            return {"account_id": request.payload["account_id"], "status": "SERVICE_BOUNDARY_READY"}
        balance = gerchain.get_balance(request.payload["account_id"])
        return {"account_id": request.payload["account_id"], "balance": balance}

    def escrow_information(request: BoundaryRequest) -> Mapping[str, Any]:
        if gerchain is None:
            return {"status": "SERVICE_BOUNDARY_READY"}
        return {"escrow": gerchain.get_escrow_state()}

    center.register("asset-information", asset_information)
    center.register("account-balance", account_balance)
    center.register("escrow-information", escrow_information)


__all__ = ["register_core_services"]

"""Composition-root handler for the frozen G-3/Core boundary.

This module is the operational bridge, not a new engine.  It accepts a
BoundaryRequest from the thin architecture adapter and delegates value
movement to an already constructed GerchainRuntime.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from architecture.contracts import BoundaryError, BoundaryRequest, BoundaryResponse
from services.gerchain_runtime import GerchainRuntime


class G3CoreRuntimeHandler:
    """Bind G-3 boundary requests to an existing authoritative Core runtime.

    The runtime is injected.  No ledger, escrow, witness, money or settlement
    engine is constructed here.
    """

    def __init__(self, runtime: GerchainRuntime):
        if not isinstance(runtime, GerchainRuntime):
            raise TypeError("runtime must be GerchainRuntime")
        self._runtime = runtime

    def __call__(self, request: BoundaryRequest) -> BoundaryResponse:
        if not isinstance(request, BoundaryRequest):
            raise BoundaryError("G-3 Core handler requires BoundaryRequest")

        payload = request.payload
        asset = payload["asset"]
        policy = payload["condition_policy"]
        escrow = payload["escrow"]
        decision = payload.get("decision")
        authorization = payload.get("authorization")

        if not self._trinity_passed(policy):
            return self._deny(request, "G-3 escrow trinity is not PASS")

        if not isinstance(decision, Mapping) or decision.get("status") != "APPROVE":
            return self._deny(request, "Core release requires APPROVE decision")

        if not isinstance(authorization, Mapping) or authorization.get("status") != "AUTHORIZED":
            return self._deny(request, "Core release requires AUTHORIZED release")

        destination = payload.get("destination")
        transaction_id = payload.get("transaction_id")
        timestamp = payload.get("timestamp")
        evidence = payload.get("evidence")

        if not destination or not transaction_id or not timestamp:
            raise BoundaryError(
                "release requires transaction_id, destination and timestamp"
            )

        result = self._runtime.release(
            transaction_id=str(transaction_id),
            destination=str(destination),
            timestamp=str(timestamp),
            evidence=evidence or {
                "type": "G3_AUTHORIZED_RELEASE",
                "asset_id": asset["asset_id"],
                "escrow_id": self._runtime.escrow_engine.escrow_id,
                "authorization": dict(authorization),
                "condition_policy": dict(policy),
                "escrow": dict(escrow),
            },
        )

        return BoundaryResponse(
            accepted=True,
            activity=request.activity,
            correlation_id=request.correlation_id,
            data={"transaction": asdict(result)},
        )

    @staticmethod
    def _trinity_passed(policy: Mapping[str, Any]) -> bool:
        if not isinstance(policy, Mapping):
            return False
        return all(
            policy.get(key) == "PASS"
            for key in ("trust", "transparency", "performance")
        )

    @staticmethod
    def _deny(request: BoundaryRequest, reason: str) -> BoundaryResponse:
        return BoundaryResponse(
            accepted=False,
            activity=request.activity,
            correlation_id=request.correlation_id,
            reason=reason,
        )


__all__ = ["G3CoreRuntimeHandler"]

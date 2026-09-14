"""Composition-root handler for the frozen G-3/Core boundary."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from architecture.contracts import BoundaryError, BoundaryRequest, BoundaryResponse
from dee_security.root_of_trust import RootOfTrust
from services.gerchain_runtime import GerchainRuntime


class G3CoreRuntimeHandler:
    """Bind G-3 boundary requests to the existing authoritative Core runtime."""

    def __init__(self, runtime: GerchainRuntime, *, root: RootOfTrust | None = None):
        if not isinstance(runtime, GerchainRuntime):
            raise TypeError("runtime must be GerchainRuntime")
        self._runtime = runtime
        self._root = root

    def __call__(self, request: BoundaryRequest) -> BoundaryResponse:
        if not isinstance(request, BoundaryRequest):
            raise BoundaryError("G-3 Core handler requires BoundaryRequest")

        payload = request.payload
        asset = payload["asset"]
        policy = payload["condition_policy"]
        escrow = payload["escrow"]
        decision = payload.get("decision")
        authorization = payload.get("authorization")
        dee_context = payload.get("_dee_context")

        if not self._trinity_passed(policy):
            return self._deny(request, "G-3 escrow trinity is not PASS")
        if not isinstance(decision, Mapping) or decision.get("status") != "APPROVE":
            return self._deny(request, "Core release requires APPROVE decision")
        if not isinstance(authorization, Mapping) or authorization.get("status") != "AUTHORIZED":
            return self._deny(request, "Core release requires AUTHORIZED release")
        if not isinstance(dee_context, Mapping):
            return self._deny(request, "Core release requires DEE authorization context")

        root = dee_context.get("root")
        owner_id = dee_context.get("owner_id")
        if not isinstance(root, RootOfTrust) or not owner_id:
            return self._deny(request, "Core release requires valid DEE root and owner")

        destination = payload.get("destination")
        source = payload.get("source")
        transaction_id = payload.get("transaction_id")
        timestamp = payload.get("timestamp")
        evidence = payload.get("evidence")
        if not destination or not transaction_id or not timestamp:
            raise BoundaryError("release requires transaction_id, destination and timestamp")
        if self._runtime.is_postgresql_authoritative and not source:
            raise BoundaryError("production release requires source account")

        trinity_proof = {key: policy.get(key) == "PASS" for key in ("trust", "transparency", "performance")}
        evidence_verified = (
            asset.get("validation_status") == "VALID"
            and bool(asset.get("verification_id"))
            and bool(asset.get("valuation_id"))
        )

        result = self._runtime.release(
            transaction_id=str(transaction_id),
            destination=str(destination),
            source=str(source) if source else None,
            idempotency_key=str(payload.get("idempotency_key")) if payload.get("idempotency_key") else None,
            timestamp=str(timestamp),
            evidence=evidence or {
                "type": "G3_AUTHORIZED_RELEASE",
                "asset_id": asset["asset_id"],
                "escrow_id": self._runtime.escrow_engine.escrow_id,
                "authorization": dict(authorization),
                "condition_policy": dict(policy),
                "escrow": dict(escrow),
            },
            root=root,
            owner_id=str(owner_id),
            authorized=True,
            evidence_verified=evidence_verified,
            trinity_proof=trinity_proof,
        )

        return BoundaryResponse(accepted=True, activity=request.activity, correlation_id=request.correlation_id, data={"transaction": asdict(result)})

    @staticmethod
    def _trinity_passed(policy: Mapping[str, Any]) -> bool:
        if not isinstance(policy, Mapping):
            return False
        return all(policy.get(key) == "PASS" for key in ("trust", "transparency", "performance"))

    @staticmethod
    def _deny(request: BoundaryRequest, reason: str) -> BoundaryResponse:
        return BoundaryResponse(accepted=False, activity=request.activity, correlation_id=request.correlation_id, reason=reason)


__all__ = ["G3CoreRuntimeHandler"]

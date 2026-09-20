"""DEE-authorized wrapper for the existing G-3/Core runtime handler.

This is a security boundary, not a second authorization or release engine.
DEE's existing RootOfTrust/ReleaseAuthorization performs the cryptographic
and replay checks; the existing G3CoreRuntimeHandler remains responsible for
calling the authoritative GerChain runtime.
"""

from __future__ import annotations

from typing import Mapping

from architecture.contracts import (
    AdapterContract,
    BoundaryError,
    BoundaryRequest,
    BoundaryResponse,
)
from dee_security import (
    AuthorizationPolicy,
    ReleaseAuthorization,
    RootOfTrust,
    authorize_release,
)
from dee_security.signing import SignedRelease
from services.g3_core_handler import G3CoreRuntimeHandler


class G3DEEAuthorizedHandler(AdapterContract):
    """Require DEE signed release authorization before Core value movement."""

    def __init__(
        self,
        core_handler: G3CoreRuntimeHandler,
        *,
        root: RootOfTrust,
        policy: AuthorizationPolicy,
        gate: ReleaseAuthorization | None = None,
    ) -> None:
        if not isinstance(core_handler, G3CoreRuntimeHandler):
            raise TypeError("core_handler must be G3CoreRuntimeHandler")
        self._core_handler = core_handler
        self._root = root
        self._policy = policy
        self._gate = gate

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        return self.__call__(request)

    def __call__(self, request: BoundaryRequest) -> BoundaryResponse:
        if not isinstance(request, BoundaryRequest):
            raise BoundaryError("DEE-authorized G-3 Core handler requires BoundaryRequest")

        payload = request.payload
        decision = payload.get("decision")
        if not isinstance(decision, Mapping) or decision.get("status") != "APPROVE":
            return BoundaryResponse(
                accepted=False,
                activity=request.activity,
                correlation_id=request.correlation_id,
                reason="DEE release requires APPROVE decision",
            )

        release = payload.get("release")
        manifest = payload.get("manifest")
        if not isinstance(release, SignedRelease):
            raise BoundaryError("DEE release requires SignedRelease")
        if not isinstance(manifest, Mapping):
            raise BoundaryError("DEE release requires signed manifest")

        try:
            authorize_release(
                root=self._root,
                policy=self._policy,
                release=release,
                manifest=manifest,
                gate=self._gate,
            )
        except Exception as exc:
            raise BoundaryError(f"DEE release authorization failed: {exc}") from exc

        authorized_payload = dict(payload)
        authorized_payload["authorization"] = {
            "status": "AUTHORIZED",
            "release_id": release.release_id,
            "manifest_hash": release.manifest_hash,
            "commit_sha": release.commit_sha,
        }
        authorized_payload["evidence"] = {
            **dict(payload.get("evidence") or {}),
            "dee_release_id": release.release_id,
            "dee_manifest_hash": release.manifest_hash,
            "dee_commit_sha": release.commit_sha,
        }

        forwarded = BoundaryRequest(
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            activity=request.activity,
            payload=authorized_payload,
            credential=request.credential,
            correlation_id=request.correlation_id,
        )
        return self._core_handler(forwarded)


__all__ = ["G3DEEAuthorizedHandler"]

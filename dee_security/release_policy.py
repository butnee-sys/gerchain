"""Release authorization for protected DEE artifacts."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .authorization import AuthorizationPolicy
from .manifest import canonical_manifest
from .root_of_trust import RootOfTrust, SecurityError
from .signing import SignedRelease, verify_release


@dataclass
class ReleaseAuthorization:
    """Fail-closed release gate with release-id replay protection."""

    _seen_release_ids: set[str] = field(default_factory=set, repr=False)

    def authorize(
        self,
        *,
        root: RootOfTrust,
        policy: AuthorizationPolicy,
        release: SignedRelease,
        manifest: Mapping[str, Any],
    ) -> None:
        protected_paths = manifest.get("protected_paths")
        if not isinstance(protected_paths, list) or not protected_paths:
            raise SecurityError("release manifest has no protected paths")
        if not all(isinstance(path, str) and policy.protects(path) for path in protected_paths):
            raise SecurityError("release contains an unprotected DEE path")

        expected_hash = manifest.get("manifest_hash")
        unsigned_manifest = {k: v for k, v in manifest.items() if k != "manifest_hash"}
        actual_hash = hashlib.sha256(canonical_manifest(unsigned_manifest)).hexdigest()
        if expected_hash != actual_hash:
            raise SecurityError("release manifest hash mismatch")

        if release.release_id in self._seen_release_ids:
            raise SecurityError("replayed release_id")
        if release.owner_id != root.owner_id:
            raise SecurityError("release owner does not match DEE owner")
        if release.commit_sha != manifest.get("commit_sha"):
            raise SecurityError("release commit does not match manifest")
        if release.manifest_hash != expected_hash:
            raise SecurityError("release is not bound to manifest hash")
        if not verify_release(root, release):
            raise SecurityError("invalid release signature")

        self._seen_release_ids.add(release.release_id)


_DEFAULT_GATE = ReleaseAuthorization()


def authorize_release(
    *,
    root: RootOfTrust,
    policy: AuthorizationPolicy,
    release: SignedRelease,
    manifest: Mapping[str, Any],
    gate: ReleaseAuthorization | None = None,
) -> None:
    (gate or _DEFAULT_GATE).authorize(
        root=root,
        policy=policy,
        release=release,
        manifest=manifest,
    )

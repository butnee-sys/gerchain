"""Fail-closed release gate for DEE protected artifacts."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

from .authorization import AuthorizationPolicy
from .manifest import canonical_manifest
from .root_of_trust import RootOfTrust, SecurityError, SignedChange
from .signing import SignedRelease, verify_release


def authorize_release(
    *,
    root: RootOfTrust,
    policy: AuthorizationPolicy,
    change: SignedChange,
    manifest: Mapping[str, Any],
    signed_release: SignedRelease | None = None,
    expected_commit_sha: str | None = None,
) -> None:
    """Authorize one protected release against the exact manifest and commit.

    A signed release is mandatory when ``signed_release`` is supplied; callers
    of this gate should pass it for production release paths. The owner change
    signature binds the manifest hash, while the release signature binds the
    release id, manifest hash, and exact commit SHA.
    """
    protected_paths = manifest.get("protected_paths")
    if not isinstance(protected_paths, list) or not protected_paths:
        raise SecurityError("release manifest has no protected paths")

    expected_hash = manifest.get("manifest_hash")
    unsigned_manifest = {k: v for k, v in manifest.items() if k != "manifest_hash"}
    actual_hash = hashlib.sha256(canonical_manifest(unsigned_manifest)).hexdigest()
    if expected_hash != actual_hash:
        raise SecurityError("release manifest hash mismatch")

    commit_sha = manifest.get("commit_sha")
    if not isinstance(commit_sha, str) or not commit_sha:
        raise SecurityError("release manifest has no commit SHA")
    if expected_commit_sha is not None and commit_sha != expected_commit_sha:
        raise SecurityError("release commit SHA mismatch")

    if change.payload_hash != expected_hash:
        raise SecurityError("release manifest is not bound to the authorized change")

    policy.check(
        root=root,
        change=change,
        paths=protected_paths,
        change_kind="release",
    )

    if signed_release is not None:
        if signed_release.owner_id != root.owner_id:
            raise SecurityError("release owner does not match Root of Trust")
        if signed_release.manifest_hash != expected_hash:
            raise SecurityError("signed release manifest hash mismatch")
        if signed_release.commit_sha != commit_sha:
            raise SecurityError("signed release commit SHA mismatch")
        if not verify_release(signed_release, root.public_key_b64):
            raise SecurityError("signed release signature is invalid")
        policy.reserve_release_id(signed_release.release_id)

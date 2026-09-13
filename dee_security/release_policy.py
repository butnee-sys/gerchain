"""Release gate for DEE protected artifacts.

A release is valid only when the signed change is valid, the protected path set
is covered by policy, and the supplied manifest matches the signed payload hash.
The signing private key remains outside the repository/build image.
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

from .authorization import AuthorizationPolicy
from .manifest import canonical_manifest
from .root_of_trust import RootOfTrust, SecurityError, SignedChange


def authorize_release(
    *,
    root: RootOfTrust,
    policy: AuthorizationPolicy,
    change: SignedChange,
    manifest: Mapping[str, Any],
) -> None:
    protected_paths = manifest.get("protected_paths")
    if not isinstance(protected_paths, list) or not protected_paths:
        raise SecurityError("release manifest has no protected paths")

    expected_hash = manifest.get("manifest_hash")
    unsigned_manifest = {k: v for k, v in manifest.items() if k != "manifest_hash"}
    actual_hash = hashlib.sha256(canonical_manifest(unsigned_manifest)).hexdigest()
    if expected_hash != actual_hash:
        raise SecurityError("release manifest hash mismatch")

    if manifest.get("commit_sha") != change.payload_hash:
        raise SecurityError("release manifest is not bound to the authorized change")

    policy.check(
        root=root,
        change=change,
        paths=protected_paths,
        change_kind="release",
    )

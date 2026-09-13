"""Explicit signing subjects for DEE changes and releases."""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .root_of_trust import RootOfTrust, SecurityError, SignedChange


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sign_change(private_key: Ed25519PrivateKey, *, owner_id: str, change_id: str, version: int, payload_hash: str) -> SignedChange:
    unsigned = SignedChange(owner_id, change_id, version, payload_hash, "")
    signature = base64.b64encode(private_key.sign(_canonical(unsigned.signing_payload()))).decode("ascii")
    return SignedChange(owner_id, change_id, version, payload_hash, signature)


@dataclass(frozen=True)
class SignedRelease:
    owner_id: str
    release_id: str
    commit_sha: str
    manifest_hash: str
    version: int
    signature: str

    def signing_payload(self) -> dict[str, Any]:
        return {
            "commit_sha": self.commit_sha,
            "manifest_hash": self.manifest_hash,
            "owner_id": self.owner_id,
            "release_id": self.release_id,
            "version": self.version,
        }


def sign_release(private_key: Ed25519PrivateKey, *, owner_id: str, release_id: str, commit_sha: str, manifest_hash: str, version: int = 1) -> SignedRelease:
    if version < 1 or not release_id or not commit_sha or not manifest_hash:
        raise SecurityError("release signing fields are incomplete")
    unsigned = SignedRelease(owner_id, release_id, commit_sha, manifest_hash, version, "")
    signature = base64.b64encode(private_key.sign(_canonical(unsigned.signing_payload()))).decode("ascii")
    return SignedRelease(owner_id, release_id, commit_sha, manifest_hash, version, signature)


def verify_release(root: RootOfTrust, release: SignedRelease) -> bool:
    if release.owner_id != root.owner_id or release.version < 1 or not release.signature:
        return False
    try:
        root._public_key.verify(base64.b64decode(release.signature.encode("ascii"), validate=True), _canonical(release.signing_payload()))
        return True
    except Exception:
        return False

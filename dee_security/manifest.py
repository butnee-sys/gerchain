"""Canonical manifests for protected DEE source/config/schema state."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


def canonical_manifest(manifest: Mapping[str, Any]) -> bytes:
    return json.dumps(
        manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_manifest(
    *,
    version: int,
    commit_sha: str,
    protected_paths: Sequence[str],
    artifact_hashes: Mapping[str, str],
    schema_version: str | None = None,
) -> dict[str, Any]:
    if version < 1:
        raise ValueError("manifest version must be positive")
    paths = sorted(set(protected_paths))
    return {
        "manifest_version": version,
        "commit_sha": commit_sha,
        "protected_paths": paths,
        "artifact_hashes": dict(sorted(artifact_hashes.items())),
        "schema_version": schema_version,
        "manifest_hash": sha256_hex(
            canonical_manifest(
                {
                    "manifest_version": version,
                    "commit_sha": commit_sha,
                    "protected_paths": paths,
                    "artifact_hashes": dict(sorted(artifact_hashes.items())),
                    "schema_version": schema_version,
                }
            )
        ),
    }

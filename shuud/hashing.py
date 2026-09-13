"""Deterministic domain hashing for the standalone SHUUD application."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _canonicalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(
        f"Unsupported type for SHUUD canonical serialization: {type(value).__name__}"
    )


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def domain_hash(domain: str, value: Any) -> str:
    """Return the same domain-separated SHA-256 construction used by GerChain."""
    hasher = hashlib.sha256()
    hasher.update(domain.encode("utf-8"))
    hasher.update(b"|")
    hasher.update(_canonical_bytes(value))
    return hasher.hexdigest()


__all__ = ["domain_hash"]

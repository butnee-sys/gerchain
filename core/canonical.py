"""
GerChain V76.0
Canonical serialization utilities.

Purpose:
- Deterministic serialization of GerChain records/state.
- Identical logical objects must produce identical canonical bytes.
- Used as the basis for cryptographic hashing and independent verification.
"""

from __future__ import annotations

import json
from typing import Any


def canonicalize(value: Any) -> Any:
    """
    Recursively convert supported Python values into deterministic,
    JSON-compatible structures.

    Rules:
    - dictionaries are represented with string keys
    - dictionary ordering is handled during serialization
    - lists/tuples are normalized to lists
    - primitive JSON values are preserved
    """
    if isinstance(value, dict):
        return {
            str(key): canonicalize(val)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [canonicalize(item) for item in value]

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    raise TypeError(
        f"Unsupported type for canonical serialization: "
        f"{type(value).__name__}"
    )


def canonical_json(value: Any) -> str:
    """
    Return deterministic JSON representation.

    Important properties:
    - sorted dictionary keys
    - compact separators
    - UTF-8 compatible
    - no insignificant whitespace
    """
    normalized = canonicalize(value)

    return json.dumps(
        normalized,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def canonical_bytes(value: Any) -> bytes:
    """
    Return canonical UTF-8 bytes.

    These bytes are the exact representation that should be hashed.
    """
    return canonical_json(value).encode("utf-8")


__all__ = [
    "canonicalize",
    "canonical_json",
    "canonical_bytes",
]
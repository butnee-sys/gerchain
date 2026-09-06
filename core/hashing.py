"""
GerChain V76.0
Domain-separated cryptographic hashing.
"""

import hashlib
from typing import Any

from core.canonical import canonical_bytes


def domain_hash(domain: str, obj: Any) -> str:
    """Domain separation бүхий SHA-256 хэш үүсгэгч."""
    payload_bytes = canonical_bytes(obj)

    hasher = hashlib.sha256()
    hasher.update(domain.encode("utf-8"))
    hasher.update(b"|")
    hasher.update(payload_bytes)

    return hasher.hexdigest()


__all__ = [
    "domain_hash",
]
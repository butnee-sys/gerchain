"""Fail-closed DEE Escrow Trinity invariant."""
from __future__ import annotations

from typing import Mapping


class TrinityError(ValueError):
    """Raised when Trust + Transparency + Performance is not PASS."""


TRINITY_KEYS = ("trust", "transparency", "performance")


def require_trinity(proof: Mapping[str, bool]) -> None:
    """Require all three Trinity conditions to be explicitly true."""
    if not isinstance(proof, Mapping):
        raise TrinityError("G-3 Trinity proof is required")
    failed = [key for key in TRINITY_KEYS if proof.get(key) is not True]
    if failed:
        raise TrinityError(f"G-3 Trinity is not PASS: {', '.join(failed)}")


__all__ = ["TRINITY_KEYS", "TrinityError", "require_trinity"]

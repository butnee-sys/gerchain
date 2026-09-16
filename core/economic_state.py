from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class EconomicStateFingerprint:
    """Identity of the canonical state relevant to one economic decision."""

    version: str
    digest: str


def fingerprint_relevant_state(*, version: str, state: Mapping[str, Any]) -> EconomicStateFingerprint:
    if not version:
        raise ValueError("state version is required")
    canonical = json.dumps(
        state,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    return EconomicStateFingerprint(version=version, digest=digest)


def state_matches(*, decision: EconomicStateFingerprint, current: EconomicStateFingerprint) -> bool:
    return decision.version == current.version and decision.digest == current.digest


__all__ = ["EconomicStateFingerprint", "fingerprint_relevant_state", "state_matches"]

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from core.hashing import domain_hash


@dataclass(frozen=True)
class EconomicStateFingerprint:
    """Identity of the canonical state relevant to one economic decision."""

    version: str
    digest: str


def fingerprint_relevant_state(*, version: str, state: Mapping[str, Any]) -> EconomicStateFingerprint:
    if not version:
        raise ValueError("state version is required")
    return EconomicStateFingerprint(
        version=version,
        digest=domain_hash("GERCHAIN:ECONOMIC-STATE", state),
    )


def state_matches(*, decision: EconomicStateFingerprint, current: EconomicStateFingerprint) -> bool:
    return decision.version == current.version and decision.digest == current.digest


__all__ = ["EconomicStateFingerprint", "fingerprint_relevant_state", "state_matches"]

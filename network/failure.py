"""
GerChain V85.0
Failure Detection.

Purpose:
- Detect witness/network node failure states.
- Represent failure deterministically.
- Keep failed nodes distinguishable from valid nodes.
- Do not modify or weaken existing V83/V84 authorization
  and cryptographic verification layers.

Principles:
- Failure detection is not consensus.
- A failed node must never count as a valid witness.
- Detection must be deterministic.
- Recovery is NOT performed in V85.0.
- Existing witness evidence remains immutable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class FailureStatus:
    node_id: str
    available: bool
    reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, str):
            raise TypeError("node_id must be a string.")
        if not self.node_id:
            raise ValueError("node_id cannot be empty.")
        if not isinstance(self.available, bool):
            raise TypeError("available must be a bool.")
        if not isinstance(self.reason, str):
            raise TypeError("reason must be a string.")

    @property
    def failed(self) -> bool:
        return not self.available

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "available": self.available,
            "failed": self.failed,
            "reason": self.reason,
        }


class FailureDetector:
    VERSION = "V85.0"

    def detect(
        self,
        node_id: str,
        available: bool,
        reason: str = "",
    ) -> FailureStatus:
        return FailureStatus(
            node_id=node_id,
            available=available,
            reason=reason,
        )

    def is_failed(self, status: FailureStatus) -> bool:
        if not isinstance(status, FailureStatus):
            raise TypeError("status must be a FailureStatus.")
        return status.failed

    def is_available(self, status: FailureStatus) -> bool:
        if not isinstance(status, FailureStatus):
            raise TypeError("status must be a FailureStatus.")
        return status.available

    def classify(self, status: FailureStatus) -> str:
        if not isinstance(status, FailureStatus):
            raise TypeError("status must be a FailureStatus.")

        if status.failed:
            return "FAILED"

        return "AVAILABLE"

    def to_dict(self, status: FailureStatus) -> Dict[str, Any]:
        if not isinstance(status, FailureStatus):
            raise TypeError("status must be a FailureStatus.")

        return {
            "version": self.VERSION,
            **status.to_dict(),
            "classification": self.classify(status),
        }


__all__ = [
    "FailureStatus",
    "FailureDetector",
]
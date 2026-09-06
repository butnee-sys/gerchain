"""
GerChain V85.1
Witness Failure Isolation.

Purpose:
- Isolate failed witness nodes from active participation.
- Preserve available witness nodes.
- Keep failure detection separate from consensus.
- Do not modify existing authorization or cryptographic layers.

Principles:
- FAILED witness -> ISOLATED.
- AVAILABLE witness -> ACTIVE.
- Isolation does not delete witness evidence.
- Isolation does not perform recovery.
- Isolation does not create consensus.
"""

from __future__ import annotations

from typing import Any, Dict

from network.failure import FailureDetector, FailureStatus


class WitnessFailureIsolation:
    VERSION = "V85.1"

    ACTIVE = "ACTIVE"
    ISOLATED = "ISOLATED"

    def __init__(self, detector: FailureDetector | None = None):
        if detector is not None and not isinstance(detector, FailureDetector):
            raise TypeError("detector must be a FailureDetector or None.")

        self.detector = detector or FailureDetector()

    def determine_status(self, status: FailureStatus) -> str:
        if not isinstance(status, FailureStatus):
            raise TypeError("status must be a FailureStatus.")

        if self.detector.is_failed(status):
            return self.ISOLATED

        return self.ACTIVE

    def is_isolated(self, status: FailureStatus) -> bool:
        return self.determine_status(status) == self.ISOLATED

    def is_active(self, status: FailureStatus) -> bool:
        return self.determine_status(status) == self.ACTIVE

    def isolate(self, status: FailureStatus) -> Dict[str, Any]:
        if not isinstance(status, FailureStatus):
            raise TypeError("status must be a FailureStatus.")

        isolation_status = self.determine_status(status)

        return {
            "version": self.VERSION,
            "node_id": status.node_id,
            "failure_status": self.detector.classify(status),
            "isolation_status": isolation_status,
            "participates_in_consensus": isolation_status == self.ACTIVE,
            "reason": status.reason,
        }


__all__ = [
    "WitnessFailureIsolation",
]
"""
GerChain V85.2
State Recovery.

Purpose:
- Recover a witness state from a trusted source state.
- Verify source-state integrity before recovery.
- Recompute the recovered state hash.
- Reject inconsistent recovery attempts.
- Keep recovery separate from consensus.

Principles:
- Only ISOLATED nodes may be recovered.
- Source state must match its expected hash.
- Recovered state is independently hashed.
- Recovery never creates consensus.
- Existing evidence is not modified.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Mapping

from network.failure import FailureStatus
from network.failure_isolation import WitnessFailureIsolation


class StateRecovery:
    VERSION = "V85.2"

    RECOVERED = "RECOVERED"
    REJECTED = "REJECTED"

    def __init__(
        self,
        isolation: WitnessFailureIsolation | None = None,
    ):
        if isolation is not None and not isinstance(
            isolation,
            WitnessFailureIsolation,
        ):
            raise TypeError(
                "isolation must be a WitnessFailureIsolation or None."
            )

        self.isolation = isolation or WitnessFailureIsolation()

    @staticmethod
    def canonical_state(state: Mapping[str, Any]) -> bytes:
        if not isinstance(state, Mapping):
            raise TypeError("state must be a mapping.")

        return json.dumps(
            dict(state),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    @classmethod
    def state_hash(cls, state: Mapping[str, Any]) -> str:
        return hashlib.sha256(
            cls.canonical_state(state)
        ).hexdigest()

    def verify_source_state(
        self,
        state: Mapping[str, Any],
        expected_hash: str,
    ) -> bool:
        if not isinstance(expected_hash, str):
            return False

        return self.state_hash(state) == expected_hash

    def recover(
        self,
        status: FailureStatus,
        source_state: Mapping[str, Any],
        expected_source_hash: str,
    ) -> Dict[str, Any]:
        if not isinstance(status, FailureStatus):
            raise TypeError("status must be a FailureStatus.")

        if not isinstance(source_state, Mapping):
            raise TypeError("source_state must be a mapping.")

        if not isinstance(expected_source_hash, str):
            raise TypeError("expected_source_hash must be a string.")

        isolation_status = self.isolation.determine_status(status)

        if isolation_status != self.isolation.ISOLATED:
            return {
                "version": self.VERSION,
                "node_id": status.node_id,
                "status": self.REJECTED,
                "reason": "NODE_IS_NOT_ISOLATED",
            }

        source_valid = self.verify_source_state(
            source_state,
            expected_source_hash,
        )

        if not source_valid:
            return {
                "version": self.VERSION,
                "node_id": status.node_id,
                "status": self.REJECTED,
                "reason": "SOURCE_STATE_HASH_MISMATCH",
            }

        recovered_state = dict(source_state)
        recovered_hash = self.state_hash(recovered_state)

        return {
            "version": self.VERSION,
            "node_id": status.node_id,
            "status": self.RECOVERED,
            "source_hash": expected_source_hash,
            "recovered_hash": recovered_hash,
            "state": recovered_state,
            "integrity_valid": (
                recovered_hash == expected_source_hash
            ),
        }


__all__ = [
    "StateRecovery",
]
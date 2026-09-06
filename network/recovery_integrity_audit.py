from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Mapping


class RecoveryIntegrityAudit:
    """
    GerChain V85.6 — Recovery Integrity Audit.

    Зорилго:
    - V85.5 recovery үр дүнг хараат бусаар шалгах.
    - Recovery-ийн хадгалсан integrity_valid утгад сохроор
      итгэхгүй байх.
    - State-ийг эх өгөгдлөөс дахин хэшлэх.
    - source_hash болон recovered state hash-ийг харьцуулах.
    - Recovery consensus болон quorum-ийн нөхцөлийг шалгах.
    - Зөрчил илэрвэл PASS гэж буруу тэмдэглэхгүй байх.
    """

    VERSION = "V85.6"

    PASS = "PASS"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"

    @staticmethod
    def canonical_state(
        state: Mapping[str, Any],
    ) -> bytes:
        """
        State-ийг deterministic canonical хэлбэрт оруулна.
        """

        if not isinstance(state, Mapping):
            raise TypeError(
                "state must be a mapping."
            )

        return json.dumps(
            dict(state),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    @classmethod
    def state_hash(
        cls,
        state: Mapping[str, Any],
    ) -> str:
        """
        State-ийн SHA-256 хэшийг дахин тооцно.
        """

        return hashlib.sha256(
            cls.canonical_state(state)
        ).hexdigest()

    @staticmethod
    def _is_sha256_hex(value: Any) -> bool:
        """
        64 тэмдэгттэй SHA-256 hex утга эсэхийг шалгана.
        """

        if not isinstance(value, str):
            return False

        if len(value) != 64:
            return False

        try:
            int(value, 16)
        except ValueError:
            return False

        return True

    def audit(
        self,
        recovery_result: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        V85.5 recovery үр дүнг хараат бусаар шалгана.
        """

        if not isinstance(
            recovery_result,
            Mapping,
        ):
            raise TypeError(
                "recovery_result must be a mapping."
            )

        result = dict(recovery_result)

        status = result.get("status")
        consensus = result.get("consensus")
        consensus_count = result.get(
            "consensus_count"
        )
        source_hash = result.get(
            "source_hash"
        )
        state = result.get("state")

        # -------------------------------------------------
        # 1. Recovery status
        # -------------------------------------------------

        if status != "RECOVERED":
            return {
                "version": self.VERSION,
                "status": self.REJECTED,
                "reason": "RECOVERY_NOT_VALID",
                "accepted": False,
                "status_valid": False,
                "consensus_valid": False,
                "source_hash_valid": False,
                "recovered_state_hash_valid": False,
                "integrity_valid": False,
            }

        # -------------------------------------------------
        # 2. Consensus
        # -------------------------------------------------

        consensus_valid = (
            consensus == "QUORUM_REACHED"
        )

        if not consensus_valid:
            return {
                "version": self.VERSION,
                "status": self.REJECTED,
                "reason": "RECOVERY_CONSENSUS_INVALID",
                "accepted": False,
                "status_valid": True,
                "consensus_valid": False,
                "source_hash_valid": False,
                "recovered_state_hash_valid": False,
                "integrity_valid": False,
            }

        # -------------------------------------------------
        # 3. Consensus count
        # -------------------------------------------------

        consensus_count_valid = (
            isinstance(consensus_count, int)
            and consensus_count > 0
        )

        if not consensus_count_valid:
            return {
                "version": self.VERSION,
                "status": self.REJECTED,
                "reason": "CONSENSUS_COUNT_INVALID",
                "accepted": False,
                "status_valid": True,
                "consensus_valid": True,
                "consensus_count_valid": False,
                "source_hash_valid": False,
                "recovered_state_hash_valid": False,
                "integrity_valid": False,
            }

        # -------------------------------------------------
        # 4. Source hash format
        # -------------------------------------------------

        source_hash_format_valid = (
            self._is_sha256_hex(source_hash)
        )

        if not source_hash_format_valid:
            return {
                "version": self.VERSION,
                "status": self.REJECTED,
                "reason": "SOURCE_HASH_INVALID",
                "accepted": False,
                "status_valid": True,
                "consensus_valid": True,
                "consensus_count_valid": True,
                "source_hash_valid": False,
                "recovered_state_hash_valid": False,
                "integrity_valid": False,
            }

        # -------------------------------------------------
        # 5. Recompute recovered state hash
        # -------------------------------------------------

        if not isinstance(state, Mapping):
            return {
                "version": self.VERSION,
                "status": self.REJECTED,
                "reason": "RECOVERED_STATE_INVALID",
                "accepted": False,
                "status_valid": True,
                "consensus_valid": True,
                "consensus_count_valid": True,
                "source_hash_valid": True,
                "recovered_state_hash_valid": False,
                "integrity_valid": False,
            }

        recovered_state_hash = self.state_hash(
            state
        )

        # -------------------------------------------------
        # 6. Independent hash comparison
        # -------------------------------------------------

        recovered_state_hash_valid = (
            recovered_state_hash == source_hash
        )

        if not recovered_state_hash_valid:
            return {
                "version": self.VERSION,
                "status": self.REJECTED,
                "reason": "RECOVERED_STATE_HASH_MISMATCH",
                "accepted": False,
                "status_valid": True,
                "consensus_valid": True,
                "consensus_count_valid": True,
                "source_hash_valid": True,
                "recovered_state_hash_valid": False,
                "integrity_valid": False,
                "source_hash": source_hash,
                "recovered_state_hash": recovered_state_hash,
            }

        # -------------------------------------------------
        # 7. Final independent decision
        # -------------------------------------------------

        return {
            "version": self.VERSION,
            "status": self.PASS,
            "reason": "RECOVERY_INTEGRITY_VALID",
            "accepted": True,
            "status_valid": True,
            "consensus_valid": True,
            "consensus_count_valid": True,
            "source_hash_valid": True,
            "recovered_state_hash_valid": True,
            "integrity_valid": True,
            "source_hash": source_hash,
            "recovered_state_hash": recovered_state_hash,
        }


__all__ = [
    "RecoveryIntegrityAudit",
]
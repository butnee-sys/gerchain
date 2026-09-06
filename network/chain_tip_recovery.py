"""
GerChain V85.3
Chain Tip Recovery.

Purpose:
- Recompute a chain tip from recovered state evidence.
- Compare the recomputed tip with a trusted chain tip.
- Reject mismatched chain tips.
- Keep chain-tip recovery separate from consensus.

Principles:
- Recovery must use recomputed evidence.
- Stored chain tips are never trusted blindly.
- A recovered state must produce the expected chain tip.
- Chain-tip mismatch means REJECTED.
- Recovery does not create consensus.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


class ChainTipRecovery:
    VERSION = "V85.3"

    VALID = "VALID"
    REJECTED = "REJECTED"

    @staticmethod
    def _canonical_state(state: Mapping[str, Any]) -> bytes:
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
            cls._canonical_state(state)
        ).hexdigest()

    @classmethod
    def compute_chain_tip(
        cls,
        manifest_hash: str,
        sequence: int,
        state: Mapping[str, Any],
        state_root: str,
    ) -> str:
        if not isinstance(manifest_hash, str):
            raise TypeError("manifest_hash must be a string.")

        if not isinstance(sequence, int):
            raise TypeError("sequence must be an integer.")

        if not isinstance(state_root, str):
            raise TypeError("state_root must be a string.")

        state_hash = cls.state_hash(state)

        payload = {
            "version": cls.VERSION,
            "manifest_hash": manifest_hash,
            "sequence": sequence,
            "final_state_hash": state_hash,
            "state_root": state_root,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(canonical).hexdigest()

    @classmethod
    def verify_chain_tip(
        cls,
        manifest_hash: str,
        sequence: int,
        state: Mapping[str, Any],
        state_root: str,
        expected_chain_tip: str,
    ) -> bool:
        if not isinstance(expected_chain_tip, str):
            return False

        computed = cls.compute_chain_tip(
            manifest_hash,
            sequence,
            state,
            state_root,
        )

        return computed == expected_chain_tip

    @classmethod
    def recover(
        cls,
        manifest_hash: str,
        sequence: int,
        recovered_state: Mapping[str, Any],
        state_root: str,
        trusted_chain_tip: str,
    ) -> dict[str, Any]:
        if not isinstance(trusted_chain_tip, str):
            raise TypeError(
                "trusted_chain_tip must be a string."
            )

        computed_chain_tip = cls.compute_chain_tip(
            manifest_hash,
            sequence,
            recovered_state,
            state_root,
        )

        valid = computed_chain_tip == trusted_chain_tip

        return {
            "version": cls.VERSION,
            "status": cls.VALID if valid else cls.REJECTED,
            "computed_chain_tip": computed_chain_tip,
            "trusted_chain_tip": trusted_chain_tip,
            "chain_tip_valid": valid,
        }


__all__ = [
    "ChainTipRecovery",
]
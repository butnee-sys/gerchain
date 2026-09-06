from __future__ import annotations

from typing import Any, Dict, Mapping

from persistence.chain_tip_anchor import ChainTipAnchor


class AnchorRecovery:
    """
    GerChain V85.4 — Anchor Recovery.

    Зорилго:
    - Сэргээгдсэн Chain Tip-ийг итгэмжлэгдсэн Anchor-той шалгах.
    - Anchor-ийн hash-ийг эх өгөгдлөөс дахин тооцох.
    - Previous Tip -> Current Tip холбоосыг шалгах.
    - Anchor Recovery-г VALID / REJECTED гэж шийдэх.
    """

    VERSION = "V85.4"
    VALID = "VALID"
    REJECTED = "REJECTED"

    @classmethod
    def verify_anchor(
        cls,
        anchor_data: Mapping[str, Any],
        recovered_chain_tip: str,
        expected_previous_tip: str | None = None,
    ) -> Dict[str, Any]:
        if not isinstance(anchor_data, Mapping):
            raise TypeError("anchor_data must be a mapping.")

        if not isinstance(recovered_chain_tip, str):
            raise TypeError(
                "recovered_chain_tip must be a string."
            )

        if (
            expected_previous_tip is not None
            and not isinstance(expected_previous_tip, str)
        ):
            raise TypeError(
                "expected_previous_tip must be a string or None."
            )

        try:
            anchor = ChainTipAnchor.from_dict(
                dict(anchor_data)
            )
        except (TypeError, ValueError, KeyError) as exc:
            return {
                "version": cls.VERSION,
                "status": cls.REJECTED,
                "reason": "ANCHOR_INVALID",
                "accepted": False,
                "chain_tip_valid": False,
                "previous_tip_valid": False,
                "anchor_hash_valid": False,
                "error": str(exc),
            }

        chain_tip_valid = anchor.matches(
            recovered_chain_tip
        )

        previous_tip_valid = (
            expected_previous_tip is None
            or anchor.previous_tip == expected_previous_tip
        )

        anchor_hash_valid = (
            anchor.anchor_hash
            == anchor.compute_anchor_hash()
        )

        accepted = (
            chain_tip_valid
            and previous_tip_valid
            and anchor_hash_valid
        )

        return {
            "version": cls.VERSION,
            "status": (
                cls.VALID
                if accepted
                else cls.REJECTED
            ),
            "chain_tip_valid": chain_tip_valid,
            "previous_tip_valid": previous_tip_valid,
            "anchor_hash_valid": anchor_hash_valid,
            "accepted": accepted,
            "chain_tip": anchor.chain_tip,
            "previous_tip": anchor.previous_tip,
            "anchor_hash": anchor.anchor_hash,
        }


__all__ = ["AnchorRecovery"]

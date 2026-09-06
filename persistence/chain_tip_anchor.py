"""
GerChain V79.9
Persistent Chain Tip Anchor with History Integrity.

Purpose:
- Persistent CHAIN_TIP Anchor хадгалах.
- Previous Tip -> Current Tip холбоос хадгалах.
- Anchor hash-ийг deterministic байдлаар тооцох.
- Нэг Anchor-ийг бие даан баталгаажуулах.
- Олон Anchor-ийн бүх түүхийг эхнээс нь шалгах.
- Anchor устгал, дараалал солилт, Tip tamper,
  hash tamper-ийг илрүүлэх.
- V79.7/V79.8-ийн үндсэн боломжуудыг хадгалах.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.canonical import canonical_bytes
from core.hashing import domain_hash


class ChainTipAnchor:
    """
    Persistent Chain Tip Anchor.

    V79.9:

        Anchor_0:
            previous_tip = None
            chain_tip = TIP_0

        Anchor_1:
            previous_tip = TIP_0
            chain_tip = TIP_1

        Anchor_2:
            previous_tip = TIP_1
            chain_tip = TIP_2
    """

    VERSION = "V79.8"

    LEGACY_VERSIONS = {
        "V79.7",
    }

    def __init__(
        self,
        chain_tip: str,
        previous_tip: Optional[str] = None,
    ):
        self._validate_chain_tip(
            chain_tip,
            "chain_tip",
        )

        if previous_tip is not None:
            self._validate_chain_tip(
                previous_tip,
                "previous_tip",
            )

        self.chain_tip = chain_tip
        self.previous_tip = previous_tip

    @staticmethod
    def _validate_chain_tip(
        value: str,
        field_name: str,
    ) -> None:

        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string."
            )

        if len(value) != 64:
            raise ValueError(
                f"{field_name} must be a "
                "64-character SHA-256 hex string."
            )

        try:
            int(value, 16)
        except ValueError as exc:
            raise ValueError(
                f"{field_name} must contain only "
                "hexadecimal characters."
            ) from exc

    def compute_anchor_hash(self) -> str:
        """
        Previous Tip + Current Tip-ээс
        deterministic Anchor hash үүсгэнэ.
        """

        return domain_hash(
            "CHAIN_TIP_ANCHOR",
            {
                "previous_tip": self.previous_tip,
                "chain_tip": self.chain_tip,
            },
        )

    @property
    def anchor_hash(self) -> str:
        """Canonical Anchor hash."""

        return self.compute_anchor_hash()

    def to_dict(self) -> Dict[str, Any]:
        """
        Anchor-ийг deterministic dictionary болгоно.
        """

        return {
            "version": self.VERSION,
            "previous_tip": self.previous_tip,
            "chain_tip": self.chain_tip,
            "anchor_hash": self.anchor_hash,
        }

    def to_bytes(self) -> bytes:
        """
        Anchor-ийг canonical UTF-8 байт
        болгон сериалчилна.
        """

        return canonical_bytes(
            self.to_dict()
        )

    def save(
        self,
        path: str | Path,
    ) -> None:
        """
        Anchor-ийг дискэнд хадгална.
        """

        target = Path(path)

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_bytes(
            self.to_bytes()
        )

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> "ChainTipAnchor":
        """
        Dictionary-ээс Anchor сэргээнэ.
        """

        if not isinstance(data, dict):
            raise TypeError(
                "Anchor data must be a dictionary."
            )

        version = data.get("version")

        if version not in (
            cls.VERSION,
            *cls.LEGACY_VERSIONS,
        ):
            raise ValueError(
                "Unsupported Chain Tip Anchor version."
            )

        if "chain_tip" not in data:
            raise ValueError(
                "Missing chain_tip."
            )

        previous_tip = data.get(
            "previous_tip",
            None,
        )

        anchor = cls(
            chain_tip=data["chain_tip"],
            previous_tip=previous_tip,
        )

        stored_anchor_hash = data.get(
            "anchor_hash"
        )

        if version == cls.VERSION:

            if stored_anchor_hash is None:
                raise ValueError(
                    "Missing anchor_hash."
                )

            if (
                stored_anchor_hash
                != anchor.anchor_hash
            ):
                raise ValueError(
                    "Anchor hash mismatch."
                )

        return anchor

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
    ) -> "ChainTipAnchor":
        """
        Canonical JSON байтаас Anchor сэргээнэ.
        """

        if not isinstance(data, bytes):
            raise TypeError(
                "Anchor data must be bytes."
            )

        try:
            decoded = json.loads(
                data.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ValueError(
                "Invalid Chain Tip Anchor encoding."
            ) from exc

        return cls.from_dict(
            decoded
        )

    @classmethod
    def load(
        cls,
        path: str | Path,
    ) -> "ChainTipAnchor":
        """
        Дискнээс Anchor сэргээнэ.
        """

        source = Path(path)

        return cls.from_bytes(
            source.read_bytes()
        )

    def matches(
        self,
        chain_tip: str,
    ) -> bool:
        """
        Current Chain Tip таарч байгаа эсэх.
        """

        return self.chain_tip == chain_tip

    def verify(
        self,
        chain_tip: str,
    ) -> bool:
        """
        Нэг Anchor-ийн бүрэн шалгалт.
        """

        return (
            self.matches(chain_tip)
            and self.anchor_hash
            == self.compute_anchor_hash()
        )

    def verify_link(
        self,
        previous_tip: Optional[str],
        chain_tip: str,
    ) -> bool:
        """
        Previous Tip -> Current Tip холбоосыг
        бүрэн шалгана.
        """

        if self.previous_tip != previous_tip:
            return False

        if self.chain_tip != chain_tip:
            return False

        return (
            self.anchor_hash
            == self.compute_anchor_hash()
        )

    @classmethod
    def verify_history(
        cls,
        anchors: List[Dict[str, Any]],
    ) -> bool:
        """
        Anchor history-г эхнээс нь
        бие даан шалгана.

        Дүрэм:

            Anchor_0.previous_tip = None

            Anchor_N.previous_tip
                =
            Anchor_(N-1).chain_tip

        Мөн Anchor бүрийн hash-ийг
        эх өгөгдлөөс дахин тооцно.
        """

        if not isinstance(anchors, list):
            return False

        if not anchors:
            return False

        previous_tip: Optional[str] = None

        for anchor_data in anchors:

            if not isinstance(
                anchor_data,
                dict,
            ):
                return False

            try:
                anchor = cls.from_dict(
                    anchor_data
                )
            except (
                TypeError,
                ValueError,
                KeyError,
            ):
                return False

            if anchor.previous_tip != previous_tip:
                return False

            if not anchor.verify_link(
                previous_tip,
                anchor.chain_tip,
            ):
                return False

            previous_tip = anchor.chain_tip

        return True


__all__ = [
    "ChainTipAnchor",
]
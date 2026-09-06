"""
GerChain V80.3
Unified Independent Verifier.

Purpose:
- Witness-ийн криптографийн бүрэн бүтэн байдлыг шалгах.
- Escrow-ийн утгын бүрэн бүтэн байдлыг шалгах.
- Money-ийн утгын бүрэн бүтэн байдлыг шалгах.
- Гурван шалгалтыг нэг бие даасан шалгалтын цэгт нэгтгэх.
- Creator Engine-ээс хараат бус байх.
- Хэш зөв байсан ч утгын хувьд буруу
  мөнгөн шилжилтийг REJECT хийх.

Compatibility:
- V80.0-ийн үндсэн report version-г хадгална.
- V80.3 мөнгөний semantic давхаргыг тусдаа
  version талбараар илэрхийлнэ.
"""

from __future__ import annotations

from typing import Any, Dict

from verifier.escrow_semantic_verifier import (
    EscrowSemanticVerifier,
)
from verifier.independent_verifier import (
    IndependentVerifier,
)
from verifier.money_semantic_verifier import (
    MoneySemanticVerifier,
)


class V80IndependentVerifier:
    """
    GerChain-ийн нэгдсэн бие даасан шалгагч.

    Шалгалтын дараалал:

        1. Witness cryptographic verification
        2. Escrow semantic verification
        3. Money semantic verification

    Аль нэг нь REJECT бол нийт шалгалт REJECT.

    V80.0-ийн үндсэн API compatibility хадгалагдана.
    V80.3 money semantic layer нэмэгдэнэ.
    """

    # -------------------------------------------------
    # Version compatibility
    # -------------------------------------------------

    VERSION = "V80.0"
    MONEY_SEMANTIC_VERSION = "V80.3"

    def __init__(self):
        self.witness_verifier = IndependentVerifier()
        self.escrow_verifier = EscrowSemanticVerifier()
        self.money_verifier = MoneySemanticVerifier()

    def verify_bundle(
        self,
        bundle: Dict[str, Any],
    ) -> bool:
        """
        Bundle-ийг бүрэн бие даан шалгана.
        """

        if not isinstance(bundle, dict):
            return False

        # -------------------------------------------------
        # STEP 1
        # Witness cryptographic verification
        # -------------------------------------------------

        witness_ok = (
            self.witness_verifier.verify_bundle(
                bundle
            )
        )

        if not witness_ok:
            return False

        # -------------------------------------------------
        # STEP 2
        # Escrow semantic verification
        # -------------------------------------------------

        escrow_ok = (
            self.escrow_verifier.verify(
                bundle
            )
        )

        if not escrow_ok:
            return False

        # -------------------------------------------------
        # STEP 3
        # Money semantic verification
        # -------------------------------------------------

        money_ok = (
            self.money_verifier.verify(
                bundle
            )
        )

        if not money_ok:
            return False

        return True

    def verify_bytes(
        self,
        data_bytes: bytes,
    ) -> bool:
        """
        Сериализлагдсан Witness bundle-ийг
        шууд бие даан шалгана.
        """

        if not isinstance(data_bytes, bytes):
            return False

        try:
            import json

            bundle = json.loads(
                data_bytes.decode("utf-8")
            )

        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            return False

        return self.verify_bundle(bundle)

    def verify_with_report(
        self,
        bundle: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Шалгалтын дүнг дэлгэрэнгүй тайлангаар буцаана.

        V80.0 compatibility:

        {
            "version": "V80.0",
            ...
        }

        V80.3 нэмэлт давхарга:

        {
            "money_semantic_version": "V80.3",
            "money_semantic": True/False
        }
        """

        if not isinstance(bundle, dict):
            return {
                "version": self.VERSION,
                "money_semantic_version": (
                    self.MONEY_SEMANTIC_VERSION
                ),
                "witness_cryptographic": False,
                "escrow_semantic": False,
                "money_semantic": False,
                "overall": False,
            }

        # -------------------------------------------------
        # STEP 1
        # Witness cryptographic verification
        # -------------------------------------------------

        witness_ok = (
            self.witness_verifier.verify_bundle(
                bundle
            )
        )

        # -------------------------------------------------
        # STEP 2
        # Escrow semantic verification
        # -------------------------------------------------

        if witness_ok:
            escrow_ok = (
                self.escrow_verifier.verify(
                    bundle
                )
            )
        else:
            escrow_ok = False

        # -------------------------------------------------
        # STEP 3
        # Money semantic verification
        # -------------------------------------------------

        if witness_ok and escrow_ok:
            money_ok = (
                self.money_verifier.verify(
                    bundle
                )
            )
        else:
            money_ok = False

        # -------------------------------------------------
        # FINAL REPORT
        # -------------------------------------------------

        return {
            "version": self.VERSION,
            "money_semantic_version": (
                self.MONEY_SEMANTIC_VERSION
            ),
            "witness_cryptographic": witness_ok,
            "escrow_semantic": escrow_ok,
            "money_semantic": money_ok,
            "overall": (
                witness_ok
                and escrow_ok
                and money_ok
            ),
        }


__all__ = [
    "V80IndependentVerifier",
]
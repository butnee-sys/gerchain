"""
GerChain V81.0
Network Witness Node.

Purpose:
- Сүлжээний нэг Witness Node-ийн үндсэн бүтэц.
- Bundle хүлээн авах.
- V80 Independent Verifier-ээр бие даан шалгах.
- Зөв bundle-ийг хүлээн авах.
- Буруу bundle-ийг татгалзах.
- Creator Engine-ийн өөрийн баталгаанд найдахгүй байх.

V81.0:
- Нэг зангилааны network boundary.
- Олон зангилааны consensus хараахан оруулаагүй.
"""

from __future__ import annotations

import copy
from typing import Any, Dict

from verifier.v80_independent_verifier import (
    V80IndependentVerifier,
)


class WitnessNode:
    """
    GerChain V81.0 Witness Node.

    Node-ийн үндсэн үүрэг:

        bundle
          ↓
        Independent Verification
          ↓
        PASS → accept
        FAIL → reject
    """

    VERSION = "V81.0"

    def __init__(
        self,
        node_id: str,
    ):
        if not isinstance(
            node_id,
            str,
        ):
            raise TypeError(
                "node_id must be a string."
            )

        if not node_id:
            raise ValueError(
                "node_id cannot be empty."
            )

        self.node_id = node_id

        self.verifier = (
            V80IndependentVerifier()
        )

        self.accepted_bundles = []

        self.rejected_count = 0

    def receive_bundle(
        self,
        bundle: Dict[str, Any],
    ) -> bool:
        """
        Сүлжээнээс bundle хүлээн авч,
        бие даан шалгана.

        PASS:
            bundle-г хадгална.

        REJECT:
            bundle-г хадгалахгүй.
        """

        if not isinstance(
            bundle,
            dict,
        ):
            self.rejected_count += 1
            return False

        verified = (
            self.verifier.verify_bundle(
                bundle
            )
        )

        if not verified:
            self.rejected_count += 1
            return False

        self.accepted_bundles.append(
            copy.deepcopy(bundle)
        )

        return True

    def receive_bytes(
        self,
        data_bytes: bytes,
    ) -> bool:
        """
        Сериализлагдсан bundle хүлээн авах.

        JSON decode хийх боловч
        эцсийн шийдвэрийг
        V80 Independent Verifier гаргана.
        """

        if not isinstance(
            data_bytes,
            bytes,
        ):
            self.rejected_count += 1
            return False

        verified = (
            self.verifier.verify_bytes(
                data_bytes
            )
        )

        if not verified:
            self.rejected_count += 1
            return False

        try:
            import json

            bundle = json.loads(
                data_bytes.decode(
                    "utf-8"
                )
            )

        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            self.rejected_count += 1
            return False

        self.accepted_bundles.append(
            copy.deepcopy(bundle)
        )

        return True

    def accepted_count(self) -> int:
        """
        Хүлээн авсан зөв bundle-ийн тоо.
        """

        return len(
            self.accepted_bundles
        )

    def rejected_count_total(self) -> int:
        """
        Татгалзсан bundle-ийн тоо.
        """

        return self.rejected_count

    def status(self) -> Dict[str, Any]:
        """
        Node-ийн одоогийн төлөв.
        """

        return {
            "version": self.VERSION,
            "node_id": self.node_id,
            "accepted_bundles": (
                self.accepted_count()
            ),
            "rejected_bundles": (
                self.rejected_count_total()
            ),
        }


__all__ = [
    "WitnessNode",
]
"""
GerChain V83.0
Authorized Witness Node Registry.

Purpose:
- Зөвшөөрөгдсөн Witness Node-уудын бүртгэл.
- Node ID-ийг зөвшөөрөгдсөн эсэхийг шалгах.
- Зөвшөөрөгдөөгүй node-ийг consensus-д оруулахгүй байх суурь.
- Давхардсан node ID-г хориглох.
- Бүртгэлийн мэдээллийг тогтвортой, тодорхой хэлбэрээр өгөх.

V83.0:
- Authorization layer.
- V82.1 cryptographic verification-ийг орлохгүй.
- Authorization нь cryptographic validity-ээс тусдаа шалгагдана.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set


class AuthorizedWitnessRegistry:
    """
    Зөвшөөрөгдсөн Witness Node-уудын бүртгэл.

    Гол зарчим:

        node_id
            ↓
        authorized?
            ↓
        V82.1 cryptographic verification
            ↓
        consensus
    """

    VERSION = "V83.0"

    def __init__(
        self,
        authorized_nodes: Optional[Iterable[str]] = None,
    ):
        self._authorized_nodes: Set[str] = set()

        if authorized_nodes is not None:
            for node_id in authorized_nodes:
                self.add(node_id)

    def _validate_node_id(
        self,
        node_id: str,
    ) -> None:
        if not isinstance(node_id, str):
            raise TypeError(
                "node_id must be a string."
            )

        if not node_id:
            raise ValueError(
                "node_id cannot be empty."
            )

    def add(
        self,
        node_id: str,
    ) -> None:
        """
        Шинэ зөвшөөрөгдсөн node нэмнэ.
        """

        self._validate_node_id(node_id)

        if node_id in self._authorized_nodes:
            raise ValueError(
                f"Node already authorized: {node_id}"
            )

        self._authorized_nodes.add(
            node_id
        )

    def remove(
        self,
        node_id: str,
    ) -> None:
        """
        Зөвшөөрлийг цуцална.
        """

        self._validate_node_id(node_id)

        if node_id not in self._authorized_nodes:
            raise ValueError(
                f"Node is not authorized: {node_id}"
            )

        self._authorized_nodes.remove(
            node_id
        )

    def is_authorized(
        self,
        node_id: str,
    ) -> bool:
        """
        Node зөвшөөрөгдсөн эсэх.
        """

        if not isinstance(node_id, str):
            return False

        if not node_id:
            return False

        return (
            node_id
            in self._authorized_nodes
        )

    def count(self) -> int:
        """
        Нийт зөвшөөрөгдсөн node-ийн тоо.
        """

        return len(
            self._authorized_nodes
        )

    def node_ids(self) -> List[str]:
        """
        Зөвшөөрөгдсөн node ID-уудыг
        тогтвортой эрэмбээр буцаана.
        """

        return sorted(
            self._authorized_nodes
        )

    def verify_node(
        self,
        node_id: str,
    ) -> Dict[str, Any]:
        """
        Нэг node-ийн эрхийн шалгалт.
        """

        authorized = self.is_authorized(
            node_id
        )

        return {
            "version": self.VERSION,
            "node_id": node_id,
            "authorized": authorized,
        }

    def verify_nodes(
        self,
        node_ids: Iterable[str],
    ) -> Dict[str, Any]:
        """
        Олон node-ийн эрхийг шалгана.
        """

        results: Dict[str, bool] = {}

        for node_id in node_ids:
            if not isinstance(node_id, str):
                continue

            results[node_id] = (
                self.is_authorized(node_id)
            )

        authorized_nodes = sorted(
            node_id
            for node_id, authorized
            in results.items()
            if authorized
        )

        unauthorized_nodes = sorted(
            node_id
            for node_id, authorized
            in results.items()
            if not authorized
        )

        return {
            "version": self.VERSION,
            "authorized_count": len(
                authorized_nodes
            ),
            "unauthorized_count": len(
                unauthorized_nodes
            ),
            "authorized_nodes":
                authorized_nodes,
            "unauthorized_nodes":
                unauthorized_nodes,
            "results": results,
        }

    def status(self) -> Dict[str, Any]:
        """
        Registry-ийн одоогийн төлөв.
        """

        return {
            "version": self.VERSION,
            "authorized_count": self.count(),
            "authorized_nodes":
                self.node_ids(),
        }


__all__ = [
    "AuthorizedWitnessRegistry",
]
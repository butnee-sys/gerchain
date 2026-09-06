"""
GerChain V82.0
Multi-Node Witness Network.

Purpose:
- Олон Witness Node бүртгэх.
- Нэг bundle-ийг олон node-д дамжуулах.
- Node бүр өөрийн Independent Verifier-ээр шалгах.
- ACCEPT / REJECT үр дүнг бүртгэх.
- Quorum буюу зөвшилцлийн босгыг шалгах.

V82.0:
- Олон зангилааны үндсэн хөдөлгүүр.
- Node бүр бие даасан verification хийнэ.
- Consensus-ийн тооцоолол ил тод байна.
- Authorization болон key protection дараагийн шатанд.
"""

from __future__ import annotations

from typing import Any, Dict, List

from network.node import WitnessNode


class MultiNodeNetwork:
    """
    GerChain V82.0 олон зангилааны сүлжээ.

    Архитектур:

        Bundle
          |
          +----> Node A -> Verify
          |
          +----> Node B -> Verify
          |
          +----> Node C -> Verify
          |
          +----> Node D -> Verify
    """

    VERSION = "V82.0"

    def __init__(
        self,
        quorum: int = 2,
    ):
        if not isinstance(quorum, int):
            raise TypeError(
                "quorum must be an integer."
            )

        if quorum < 1:
            raise ValueError(
                "quorum must be at least 1."
            )

        self.quorum = quorum

        self.nodes: Dict[
            str,
            WitnessNode,
        ] = {}

        self.results: List[
            Dict[str, Any]
        ] = []

    def add_node(
        self,
        node: WitnessNode,
    ) -> None:
        """
        Сүлжээнд Witness Node нэмнэ.
        """

        if not isinstance(
            node,
            WitnessNode,
        ):
            raise TypeError(
                "node must be a WitnessNode."
            )

        if node.node_id in self.nodes:
            raise ValueError(
                f"Node already exists: "
                f"{node.node_id}"
            )

        self.nodes[
            node.node_id
        ] = node

    def remove_node(
        self,
        node_id: str,
    ) -> None:
        """
        Node-ийг сүлжээнээс хасна.
        """

        if node_id not in self.nodes:
            raise ValueError(
                f"Unknown node: {node_id}"
            )

        del self.nodes[
            node_id
        ]

    def node_count(self) -> int:
        """
        Сүлжээнд байгаа node-ийн тоо.
        """

        return len(
            self.nodes
        )

    def broadcast(
        self,
        bundle: Dict[str, Any],
    ) -> Dict[str, bool]:
        """
        Bundle-ийг бүх node-д дамжуулна.

        Node бүр өөрийн verification
        хийж шийдвэр гаргана.
        """

        results = {}

        for node_id, node in self.nodes.items():

            accepted = (
                node.receive_bundle(
                    bundle
                )
            )

            results[
                node_id
            ] = accepted

        self.results.append(
            {
                "bundle": bundle,
                "results": results.copy(),
            }
        )

        return results

    def accepted_nodes(
        self,
        results: Dict[str, bool],
    ) -> List[str]:
        """
        ACCEPT хийсэн node-уудын жагсаалт.
        """

        return [
            node_id
            for node_id, accepted
            in results.items()
            if accepted
        ]

    def rejected_nodes(
        self,
        results: Dict[str, bool],
    ) -> List[str]:
        """
        REJECT хийсэн node-уудын жагсаалт.
        """

        return [
            node_id
            for node_id, accepted
            in results.items()
            if not accepted
        ]

    def accepted_count(
        self,
        results: Dict[str, bool],
    ) -> int:
        """
        ACCEPT хийсэн node-ийн тоо.
        """

        return len(
            self.accepted_nodes(
                results
            )
        )

    def rejected_count(
        self,
        results: Dict[str, bool],
    ) -> int:
        """
        REJECT хийсэн node-ийн тоо.
        """

        return len(
            self.rejected_nodes(
                results
            )
        )

    def has_quorum(
        self,
        results: Dict[str, bool],
    ) -> bool:
        """
        ACCEPT хийсэн node-ийн тоо
        quorum-д хүрсэн эсэхийг шалгана.

        Чухал:
        - quorum-д хүрсэн гэж үзэхийн
          тулд бодитоор ACCEPT хийсэн
          node-уудыг тоолно.
        - Node өөрөө өөртөө quorum
          зохиож өгөхгүй.
        """

        return (
            self.accepted_count(
                results
            )
            >= self.quorum
        )

    def consensus_result(
        self,
        results: Dict[str, bool],
    ) -> str:
        """
        Олон node-ийн үр дүнг ангилна.

        QUORUM_REACHED:
            quorum хүрсэн.

        QUORUM_NOT_REACHED:
            quorum хүрээгүй.

        NO_NODES:
            node байхгүй.
        """

        if not results:
            return "NO_NODES"

        if self.has_quorum(
            results
        ):
            return "QUORUM_REACHED"

        return "QUORUM_NOT_REACHED"

    def verify_network(
        self,
        bundle: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Bundle-ийг бүх node-д өгч,
        нэгдсэн network verification report
        үүсгэнэ.

        Анхаарах:
        Энэ шатанд quorum хүрсэн нь
        зөвхөн node verification-ийн
        тоон үр дүн.

        Криптографийн consensus,
        authorized witness set,
        chain-tip consensus
        дараагийн шатанд нэмэгдэнэ.
        """

        results = self.broadcast(
            bundle
        )

        accepted = self.accepted_nodes(
            results
        )

        rejected = self.rejected_nodes(
            results
        )

        return {
            "version": self.VERSION,
            "quorum": self.quorum,
            "node_count": self.node_count(),
            "accepted_count": len(
                accepted
            ),
            "rejected_count": len(
                rejected
            ),
            "accepted_nodes": accepted,
            "rejected_nodes": rejected,
            "consensus": (
                self.consensus_result(
                    results
                )
            ),
            "results": results,
        }

    def status(self) -> Dict[str, Any]:
        """
        Сүлжээний одоогийн төлөв.
        """

        return {
            "version": self.VERSION,
            "node_count": self.node_count(),
            "quorum": self.quorum,
            "node_ids": sorted(
                self.nodes.keys()
            ),
            "verification_rounds": len(
                self.results
            ),
        }


__all__ = [
    "MultiNodeNetwork",
]
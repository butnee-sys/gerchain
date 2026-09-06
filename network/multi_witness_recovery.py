from __future__ import annotations

from typing import Any, Dict, List, Mapping

from network.consensus import MultiNodeConsensus


class MultiWitnessRecovery:
    """
    GerChain V85.5 — Multi-Witness Recovery.

    Зорилго:
    - Олон Witness-ийн баталгаатай үр дүнг шалгах.
    - Failed / invalid Witness-ийг recovery шийдвэрээс хасах.
    - Authorized + cryptographically valid Witness-үүдийн
      consensus-ийг recovery-ийн үндэс болгох.
    - Quorum-д хүрээгүй үед recovery-г зөвшөөрөхгүй байх.
    - Хуурамч recovery consensus үүсгэхгүй байх.
    - Recovery хийхээс өмнө эх төлөвийн хэшийг
      дахин тооцож шалгах.
    """

    VERSION = "V85.5"

    RECOVERED = "RECOVERED"
    REJECTED = "REJECTED"

    def __init__(
        self,
        consensus: MultiNodeConsensus | None = None,
    ):
        if consensus is not None and not isinstance(
            consensus,
            MultiNodeConsensus,
        ):
            raise TypeError(
                "consensus must be a MultiNodeConsensus or None."
            )

        self.consensus = consensus or MultiNodeConsensus()

    def determine_recovery_consensus(
        self,
        node_results: List[Dict[str, Any]],
        failed_nodes: List[str] | None = None,
    ) -> Dict[str, Any]:
        """
        Failed Witness-үүдийг recovery consensus-оос хасна.

        Үлдсэн node-уудын:
            authorized == True
            verified == True

        нөхцөл дээр V83.2 consensus-ийг дахин ашиглана.
        """

        if not isinstance(node_results, list):
            raise TypeError(
                "node_results must be a list."
            )

        if failed_nodes is None:
            failed_nodes = []

        if not isinstance(failed_nodes, list):
            raise TypeError(
                "failed_nodes must be a list."
            )

        failed_set = set()

        for node_id in failed_nodes:
            if not isinstance(node_id, str):
                raise TypeError(
                    "failed_nodes must contain strings."
                )
            failed_set.add(node_id)

        active_results = []

        for result in node_results:
            if not isinstance(result, dict):
                continue

            node_id = result.get("node_id")

            if not isinstance(node_id, str):
                continue

            if node_id in failed_set:
                continue

            active_results.append(result)

        consensus = self.consensus.determine_consensus(
            active_results
        )

        return {
            "version": self.VERSION,
            "failed_nodes": sorted(failed_set),
            "active_nodes": sorted(
                result["node_id"]
                for result in active_results
                if isinstance(result.get("node_id"), str)
            ),
            "active_count": len(active_results),
            "consensus": consensus["consensus"],
            "chain_tip": consensus["chain_tip"],
            "consensus_nodes": consensus["nodes"],
            "consensus_count": consensus["count"],
            "groups": consensus["groups"],
        }

    def recover(
        self,
        node_results: List[Dict[str, Any]],
        source_state: Mapping[str, Any],
        expected_source_hash: str,
        failed_nodes: List[str] | None = None,
    ) -> Dict[str, Any]:
        """
        Multi-Witness consensus-ийг үндэслэн
        recovery зөвшөөрөх эсэхийг шийднэ.

        Recovery нь зөвхөн:

            QUORUM_REACHED

        үед үргэлжилнэ.

        State hash-ийг сохроор итгэхгүй.
        Эх өгөгдлөөс дахин тооцно.
        """

        if not isinstance(source_state, Mapping):
            raise TypeError(
                "source_state must be a mapping."
            )

        if not isinstance(expected_source_hash, str):
            raise TypeError(
                "expected_source_hash must be a string."
            )

        recovery_consensus = (
            self.determine_recovery_consensus(
                node_results,
                failed_nodes,
            )
        )

        if recovery_consensus["consensus"] != "QUORUM_REACHED":
            return {
                "version": self.VERSION,
                "status": self.REJECTED,
                "reason": "RECOVERY_QUORUM_NOT_REACHED",
                "consensus": recovery_consensus["consensus"],
                "chain_tip": recovery_consensus["chain_tip"],
                "consensus_nodes": recovery_consensus[
                    "consensus_nodes"
                ],
                "consensus_count": recovery_consensus[
                    "consensus_count"
                ],
                "failed_nodes": recovery_consensus[
                    "failed_nodes"
                ],
                "active_nodes": recovery_consensus[
                    "active_nodes"
                ],
            }

        # V85.2 StateRecovery ашиглан
        # эх төлөвийн хэшийг дахин тооцож шалгана.
        from network.state_recovery import StateRecovery

        state_recovery = StateRecovery()

        state_valid = state_recovery.verify_source_state(
            source_state,
            expected_source_hash,
        )

        if not state_valid:
            return {
                "version": self.VERSION,
                "status": self.REJECTED,
                "reason": "SOURCE_STATE_HASH_MISMATCH",
                "consensus": recovery_consensus["consensus"],
                "chain_tip": recovery_consensus["chain_tip"],
                "consensus_nodes": recovery_consensus[
                    "consensus_nodes"
                ],
                "consensus_count": recovery_consensus[
                    "consensus_count"
                ],
            }

        recovered_state = dict(source_state)

        return {
            "version": self.VERSION,
            "status": self.RECOVERED,
            "consensus": recovery_consensus["consensus"],
            "chain_tip": recovery_consensus["chain_tip"],
            "consensus_nodes": recovery_consensus[
                "consensus_nodes"
            ],
            "consensus_count": recovery_consensus[
                "consensus_count"
            ],
            "failed_nodes": recovery_consensus[
                "failed_nodes"
            ],
            "active_nodes": recovery_consensus[
                "active_nodes"
            ],
            "source_hash": expected_source_hash,
            "state": recovered_state,
            "integrity_valid": True,
        }


__all__ = [
    "MultiWitnessRecovery",
]
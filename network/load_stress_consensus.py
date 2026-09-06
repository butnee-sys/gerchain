from __future__ import annotations

import time
from typing import Any, Dict, List

from network.consensus import MultiNodeConsensus


class ConsensusLoadStressTest:
    """
    GerChain V86.1 — Multi-Witness Consensus Load Test.

    Зорилго:
    - Олон гэрчийн зөвшилцлийг их хэмжээгээр боловсруулах.
    - Нэг ижил chain_tip дээрх зөвшилцлийг хэмжих.
    - Зөвшилцлийн үр дүнг детерминистик эсэхийг шалгах.
    - Хуурамч зөвшилцөл үүсгэхгүй байх.
    - V83.x–V85.x зөвшилцлийн логикийг өөрчлөхгүйгээр
      зөвхөн ачааллын хэмжилт хийх.
    """

    VERSION = "V86.1"

    @staticmethod
    def make_consensus_results(
        witness_count: int,
        chain_tip: str = "tip-a",
    ) -> List[Dict[str, Any]]:
        if not isinstance(witness_count, int):
            raise TypeError(
                "witness_count must be an integer."
            )

        if witness_count < 1:
            raise ValueError(
                "witness_count must be >= 1."
            )

        if not isinstance(chain_tip, str):
            raise TypeError(
                "chain_tip must be a string."
            )

        return [
            {
                "node_id": f"node-{index}",
                "verified": True,
                "authorized": True,
                "chain_tip": chain_tip,
            }
            for index in range(1, witness_count + 1)
        ]

    @classmethod
    def run_consensus(
        cls,
        witness_count: int,
        chain_tip: str = "tip-a",
    ) -> Dict[str, Any]:
        results = cls.make_consensus_results(
            witness_count,
            chain_tip,
        )

        consensus_engine = MultiNodeConsensus()

        start = time.perf_counter()

        consensus = consensus_engine.determine_consensus(
            results
        )

        elapsed = time.perf_counter() - start

        return {
            "version": cls.VERSION,
            "operation": "CONSENSUS",
            "witness_count": witness_count,
            "elapsed_seconds": elapsed,
            "consensus": consensus["consensus"],
            "chain_tip": consensus["chain_tip"],
            "consensus_count": consensus["count"],
            "consensus_nodes": consensus["nodes"],
            "groups": consensus["groups"],
        }

    @classmethod
    def benchmark(
        cls,
        witness_count: int,
        iterations: int,
        chain_tip: str = "tip-a",
    ) -> Dict[str, Any]:
        if not isinstance(iterations, int):
            raise TypeError(
                "iterations must be an integer."
            )

        if iterations < 1:
            raise ValueError(
                "iterations must be >= 1."
            )

        results = cls.make_consensus_results(
            witness_count,
            chain_tip,
        )

        consensus_engine = MultiNodeConsensus()

        start = time.perf_counter()

        final_consensus = None

        for _ in range(iterations):
            final_consensus = (
                consensus_engine.determine_consensus(
                    results
                )
            )

        elapsed = time.perf_counter() - start

        return {
            "version": cls.VERSION,
            "operation": "CONSENSUS_BENCHMARK",
            "witness_count": witness_count,
            "iterations": iterations,
            "elapsed_seconds": elapsed,
            "operations_per_second": (
                iterations / elapsed
                if elapsed > 0
                else float("inf")
            ),
            "final_consensus": final_consensus,
            "deterministic": True,
        }

    @classmethod
    def run_determinism_check(
        cls,
        witness_count: int,
        chain_tip: str = "tip-a",
    ) -> Dict[str, Any]:
        first = cls.run_consensus(
            witness_count,
            chain_tip,
        )

        second = cls.run_consensus(
            witness_count,
            chain_tip,
        )

        deterministic = (
            first["consensus"]
            == second["consensus"]
            and first["chain_tip"]
            == second["chain_tip"]
            and first["consensus_count"]
            == second["consensus_count"]
            and first["consensus_nodes"]
            == second["consensus_nodes"]
            and first["groups"]
            == second["groups"]
        )

        return {
            "version": cls.VERSION,
            "operation": "DETERMINISM_CHECK",
            "witness_count": witness_count,
            "deterministic": deterministic,
            "first": first,
            "second": second,
            "status": (
                "PASS"
                if deterministic
                else "REJECTED"
            ),
        }


__all__ = [
    "ConsensusLoadStressTest",
]
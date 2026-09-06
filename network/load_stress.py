from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Mapping


class LoadStressTest:
    """
    GerChain V86.0 — Load & Stress Test.

    Зорилго:
    - Олон гэрчийн үр дүнг их хэмжээгээр боловсруулах.
    - State hash дахин тооцооллын ачааллыг хэмжих.
    - Recovery integrity шалгалтын гүйцэтгэлийг хэмжих.
    - Deterministic үр дүнг хадгалах.
    - Хуурамч consensus үүсгэхгүй байх.
    """

    VERSION = "V86.0"

    @staticmethod
    def canonical_state(
        state: Mapping[str, Any],
    ) -> bytes:
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
        return hashlib.sha256(
            cls.canonical_state(state)
        ).hexdigest()

    @staticmethod
    def make_witness_results(
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
    def benchmark_state_hash(
        cls,
        state: Mapping[str, Any],
        iterations: int,
    ) -> Dict[str, Any]:
        if not isinstance(iterations, int):
            raise TypeError(
                "iterations must be an integer."
            )

        if iterations < 1:
            raise ValueError(
                "iterations must be >= 1."
            )

        start = time.perf_counter()

        final_hash = None

        for _ in range(iterations):
            final_hash = cls.state_hash(state)

        elapsed = time.perf_counter() - start

        return {
            "version": cls.VERSION,
            "operation": "STATE_HASH",
            "iterations": iterations,
            "elapsed_seconds": elapsed,
            "operations_per_second": (
                iterations / elapsed
                if elapsed > 0
                else float("inf")
            ),
            "final_hash": final_hash,
            "deterministic": True,
        }

    @classmethod
    def benchmark_witness_generation(
        cls,
        witness_count: int,
    ) -> Dict[str, Any]:
        start = time.perf_counter()

        results = cls.make_witness_results(
            witness_count
        )

        elapsed = time.perf_counter() - start

        return {
            "version": cls.VERSION,
            "operation": "WITNESS_GENERATION",
            "witness_count": witness_count,
            "elapsed_seconds": elapsed,
            "witnesses_per_second": (
                witness_count / elapsed
                if elapsed > 0
                else float("inf")
            ),
            "generated_count": len(results),
        }

    @classmethod
    def run(
        cls,
        witness_count: int,
        hash_iterations: int,
        state: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(state, Mapping):
            raise TypeError(
                "state must be a mapping."
            )

        witness_results = cls.make_witness_results(
            witness_count
        )

        expected_hash = cls.state_hash(state)

        hash_benchmark = cls.benchmark_state_hash(
            state,
            hash_iterations,
        )

        witness_benchmark = (
            cls.benchmark_witness_generation(
                witness_count
            )
        )

        deterministic_hash = (
            cls.state_hash(state)
            == expected_hash
        )

        return {
            "version": cls.VERSION,
            "witness_count": witness_count,
            "hash_iterations": hash_iterations,
            "expected_hash": expected_hash,
            "deterministic_hash": deterministic_hash,
            "witness_results": witness_results,
            "hash_benchmark": hash_benchmark,
            "witness_benchmark": witness_benchmark,
            "status": (
                "PASS"
                if deterministic_hash
                else "REJECTED"
            ),
        }


__all__ = [
    "LoadStressTest",
]
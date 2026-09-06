from __future__ import annotations

import time
from typing import Any, Dict, List, Mapping

from network.multi_witness_recovery import MultiWitnessRecovery
from network.recovery_integrity_audit import RecoveryIntegrityAudit


class RecoveryLoadStressTest:
    """
    GerChain V86.2 — Recovery + Integrity Load Test.

    Урсгал:
        олон гэрч
          ↓
        зөвшилцөл
          ↓
        сэргээх
          ↓
        төлөвийн хэш
          ↓
        бүрэн бүтэн байдлын аудит

    Зорилго:
    - Бодит MultiWitnessRecovery урсгалыг ачаалалтай шалгах.
    - RecoveryIntegrityAudit-ийг сэргээсэн төлөв дээр ажиллуулах.
    - Детерминистик үр дүнг шалгах.
    - Хуурамч recovery PASS үүсгэхгүй байх.
    """

    VERSION = "V86.2"

    @staticmethod
    def make_node_results(
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

    @staticmethod
    def make_state(
        sequence: int = 862,
        balance: int = 1_000_000,
    ) -> Dict[str, Any]:
        if not isinstance(sequence, int):
            raise TypeError(
                "sequence must be an integer."
            )

        if not isinstance(balance, int):
            raise TypeError(
                "balance must be an integer."
            )

        return {
            "sequence": sequence,
            "balance": balance,
            "status": "RECOVERABLE",
            "escrow": 250_000,
        }

    @classmethod
    def run(
        cls,
        witness_count: int,
        state: Mapping[str, Any],
        chain_tip: str = "tip-a",
        failed_nodes: List[str] | None = None,
    ) -> Dict[str, Any]:
        if not isinstance(state, Mapping):
            raise TypeError(
                "state must be a mapping."
            )

        if failed_nodes is None:
            failed_nodes = []

        node_results = cls.make_node_results(
            witness_count,
            chain_tip,
        )

        recovery_engine = MultiWitnessRecovery()
        audit_engine = RecoveryIntegrityAudit()

        expected_source_hash = (
            RecoveryIntegrityAudit.state_hash(state)
        )

        start = time.perf_counter()

        recovery_result = recovery_engine.recover(
            node_results=node_results,
            source_state=state,
            expected_source_hash=expected_source_hash,
            failed_nodes=failed_nodes,
        )

        audit_result = audit_engine.audit(
            recovery_result
        )

        elapsed = time.perf_counter() - start

        accepted = (
            recovery_result.get("status") == "RECOVERED"
            and audit_result.get("status") == "PASS"
            and audit_result.get("accepted") is True
        )

        return {
            "version": cls.VERSION,
            "operation": "RECOVERY_INTEGRITY",
            "witness_count": witness_count,
            "failed_nodes": list(failed_nodes),
            "chain_tip": chain_tip,
            "elapsed_seconds": elapsed,
            "recovery": recovery_result,
            "audit": audit_result,
            "status": (
                "PASS"
                if accepted
                else "REJECTED"
            ),
        }

    @classmethod
    def benchmark(
        cls,
        witness_count: int,
        iterations: int,
        state: Mapping[str, Any],
        chain_tip: str = "tip-a",
        failed_nodes: List[str] | None = None,
    ) -> Dict[str, Any]:
        if not isinstance(iterations, int):
            raise TypeError(
                "iterations must be an integer."
            )

        if iterations < 1:
            raise ValueError(
                "iterations must be >= 1."
            )

        if failed_nodes is None:
            failed_nodes = []

        node_results = cls.make_node_results(
            witness_count,
            chain_tip,
        )

        recovery_engine = MultiWitnessRecovery()
        audit_engine = RecoveryIntegrityAudit()

        expected_source_hash = (
            RecoveryIntegrityAudit.state_hash(state)
        )

        start = time.perf_counter()

        final_recovery = None
        final_audit = None

        for _ in range(iterations):
            final_recovery = recovery_engine.recover(
                node_results=node_results,
                source_state=state,
                expected_source_hash=expected_source_hash,
                failed_nodes=failed_nodes,
            )

            final_audit = audit_engine.audit(
                final_recovery
            )

        elapsed = time.perf_counter() - start

        passed = (
            final_recovery is not None
            and final_audit is not None
            and final_recovery.get("status") == "RECOVERED"
            and final_audit.get("status") == "PASS"
            and final_audit.get("accepted") is True
        )

        return {
            "version": cls.VERSION,
            "operation": "RECOVERY_INTEGRITY_BENCHMARK",
            "witness_count": witness_count,
            "iterations": iterations,
            "elapsed_seconds": elapsed,
            "operations_per_second": (
                iterations / elapsed
                if elapsed > 0
                else float("inf")
            ),
            "final_recovery": final_recovery,
            "final_audit": final_audit,
            "deterministic": passed,
            "status": (
                "PASS"
                if passed
                else "REJECTED"
            ),
        }


__all__ = [
    "RecoveryLoadStressTest",
]
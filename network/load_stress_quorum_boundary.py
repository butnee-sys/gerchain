from __future__ import annotations

import time
from typing import Any, Dict, List, Mapping

from network.multi_witness_recovery import MultiWitnessRecovery
from network.recovery_integrity_audit import RecoveryIntegrityAudit


class QuorumBoundaryLoadStressTest:
    """
    GerChain V86.4 — Recovery Failure / Quorum Boundary Load Test.

    Зорилго:
    - Зөвшилцлийн босго хүрэхгүй нөхцөлийг зориудаар үүсгэх.
    - Олон гэрч бүгд доголдсон үед recovery-г зөв REJECTED болгох.
    - Зөвшилцөлгүй recovery дээр integrity audit PASS өгөхгүй байх.
    - Хуурамч recovery болон хуурамч consensus үүсгэхгүй байх.
    - Олон удаагийн бүтэлгүй recovery-г ачааллын дор шалгах.

    Үндсэн зарчим:
        QUORUM_REACHED  -> recovery үргэлжилнэ
        NO_QUORUM       -> recovery REJECTED
        RECOVERY REJECTED -> integrity audit PASS биш
    """

    VERSION = "V86.4"

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
    def make_failed_nodes(
        witness_count: int,
        failure_count: int,
    ) -> List[str]:
        if not isinstance(witness_count, int):
            raise TypeError(
                "witness_count must be an integer."
            )

        if not isinstance(failure_count, int):
            raise TypeError(
                "failure_count must be an integer."
            )

        if witness_count < 1:
            raise ValueError(
                "witness_count must be >= 1."
            )

        if failure_count < 0:
            raise ValueError(
                "failure_count must be >= 0."
            )

        if failure_count > witness_count:
            raise ValueError(
                "failure_count cannot exceed witness_count."
            )

        return [
            f"node-{index}"
            for index in range(1, failure_count + 1)
        ]

    @staticmethod
    def make_state(
        sequence: int = 864,
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
        failure_count: int,
        state: Mapping[str, Any],
        chain_tip: str = "tip-a",
    ) -> Dict[str, Any]:
        if not isinstance(state, Mapping):
            raise TypeError(
                "state must be a mapping."
            )

        failed_nodes = cls.make_failed_nodes(
            witness_count,
            failure_count,
        )

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

        quorum_reached = (
            recovery_result.get("consensus")
            == "QUORUM_REACHED"
        )

        recovery_rejected = (
            recovery_result.get("status")
            == "REJECTED"
        )

        audit_not_pass = (
            audit_result.get("status")
            != "PASS"
        )

        safe_rejection = (
            not quorum_reached
            and recovery_rejected
            and audit_not_pass
        )

        return {
            "version": cls.VERSION,
            "operation": "QUORUM_BOUNDARY",
            "witness_count": witness_count,
            "failure_count": failure_count,
            "failed_nodes": failed_nodes,
            "active_count": (
                witness_count - failure_count
            ),
            "chain_tip": chain_tip,
            "elapsed_seconds": elapsed,
            "recovery": recovery_result,
            "audit": audit_result,
            "quorum_reached": quorum_reached,
            "recovery_rejected": recovery_rejected,
            "audit_not_pass": audit_not_pass,
            "safe_rejection": safe_rejection,
            "status": (
                "PASS"
                if safe_rejection
                else "REJECTED"
            ),
        }

    @classmethod
    def benchmark(
        cls,
        witness_count: int,
        failure_count: int,
        iterations: int,
        state: Mapping[str, Any],
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

        if not isinstance(state, Mapping):
            raise TypeError(
                "state must be a mapping."
            )

        failed_nodes = cls.make_failed_nodes(
            witness_count,
            failure_count,
        )

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

        safe_rejection = (
            final_recovery is not None
            and final_audit is not None
            and final_recovery.get("status")
            == "REJECTED"
            and final_recovery.get("consensus")
            != "QUORUM_REACHED"
            and final_audit.get("status")
            != "PASS"
        )

        return {
            "version": cls.VERSION,
            "operation": "QUORUM_BOUNDARY_BENCHMARK",
            "witness_count": witness_count,
            "failure_count": failure_count,
            "iterations": iterations,
            "failed_nodes": failed_nodes,
            "active_count": (
                witness_count - failure_count
            ),
            "elapsed_seconds": elapsed,
            "operations_per_second": (
                iterations / elapsed
                if elapsed > 0
                else float("inf")
            ),
            "final_recovery": final_recovery,
            "final_audit": final_audit,
            "safe_rejection": safe_rejection,
            "status": (
                "PASS"
                if safe_rejection
                else "REJECTED"
            ),
        }


__all__ = [
    "QuorumBoundaryLoadStressTest",
]
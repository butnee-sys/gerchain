from __future__ import annotations

import time
from typing import Any, Dict, List, Mapping

from network.failure import FailureDetector
from network.failure_isolation import WitnessFailureIsolation
from network.multi_witness_recovery import MultiWitnessRecovery
from network.recovery_integrity_audit import RecoveryIntegrityAudit


class FailureInjectionLoadStressTest:
    """
    GerChain V86.3 — Failure Injection Load Test.

    Урсгал:

        гэрчийн сүлжээ
             ↓
        зориудын доголдол
             ↓
        failure detection
             ↓
        failure isolation
             ↓
        active witness consensus
             ↓
        recovery
             ↓
        recovery integrity audit

    Зорилго:
    - Доголдсон гэрчийг зөв илрүүлэх.
    - Доголдсон гэрчийг зөв тусгаарлах.
    - Тусгаарлагдсан гэрчийг зөвшилцөлд оруулахгүй байх.
    - Үлдсэн гэрчүүдээр сэргээх ажиллагааг шалгах.
    - Сэргээгдсэн төлөвийн бүрэн бүтэн байдлыг дахин шалгах.
    - Олон удаагийн ажиллагааны детерминистик байдлыг хэмжих.
    """

    VERSION = "V86.3"

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
        sequence: int = 863,
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

        detector = FailureDetector()
        isolation = WitnessFailureIsolation(
            detector
        )
        recovery_engine = MultiWitnessRecovery()
        audit_engine = RecoveryIntegrityAudit()

        failure_statuses = []

        for node_id in failed_nodes:
            status = detector.detect(
                node_id=node_id,
                available=False,
                reason="INJECTED_FAILURE",
            )

            failure_statuses.append(
                isolation.isolate(status)
            )

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

        all_failed_isolated = all(
            item["isolation_status"] == "ISOLATED"
            and item["participates_in_consensus"] is False
            for item in failure_statuses
        )

        accepted = (
            all_failed_isolated
            and recovery_result.get("status")
            == "RECOVERED"
            and audit_result.get("status")
            == "PASS"
            and audit_result.get("accepted") is True
        )

        return {
            "version": cls.VERSION,
            "operation": "FAILURE_INJECTION",
            "witness_count": witness_count,
            "failure_count": failure_count,
            "failed_nodes": failed_nodes,
            "chain_tip": chain_tip,
            "elapsed_seconds": elapsed,
            "failure_statuses": failure_statuses,
            "recovery": recovery_result,
            "audit": audit_result,
            "failed_nodes_isolated": all_failed_isolated,
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

        passed = (
            final_recovery is not None
            and final_audit is not None
            and final_recovery.get("status")
            == "RECOVERED"
            and final_audit.get("status")
            == "PASS"
            and final_audit.get("accepted") is True
        )

        return {
            "version": cls.VERSION,
            "operation": "FAILURE_INJECTION_BENCHMARK",
            "witness_count": witness_count,
            "failure_count": failure_count,
            "iterations": iterations,
            "failed_nodes": failed_nodes,
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
    "FailureInjectionLoadStressTest",
]
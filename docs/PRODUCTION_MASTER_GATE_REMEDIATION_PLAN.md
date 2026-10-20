# Production Master Gate Remediation Plan

Status: **IN PROGRESS / NOT LOCKED**

This plan is based on the exact-SHA decision artifact from production master-gate run
[39415913765](https://github.com/butnee-sys/gerchain/actions/runs/39415913765), for commit
`eaaac028b009141e9c3bd77310d1cecf090ac256`.

The master gate correctly returned `NOT_LOCKED`. PostgreSQL evidence is not a substitute
for architecture-level evidence. The decision artifact reported the PostgreSQL/boot and
deep-reconciliation checks as successful, while all 17 architecture-level evidence records
were missing. This document does not change those outcomes or assert that any missing gate
has passed.

## Required architecture gates

Every gate must have (1) a named evidence artifact, (2) a reproducible verification procedure,
(3) the exact tested commit SHA, and (4) an outcome supported by the artifact. A document
that only describes intended behavior is not proof of runtime behavior.

| Gate key | Required proof | Minimum closure condition |
|---|---|---|
| `inventory_map` | Component/runtime/schema inventory | Every production entrypoint, persistence store, engine, adapter, and external boundary mapped to an owner and authority. |
| `error_duplicate_excess` | Duplicate/excess and failure-mode report | Duplicate authoritative stores, bypasses, unsafe fallbacks, and unresolved findings listed with disposition and verification. |
| `cross_store_reconciliation` | Reconciliation report + fixture/results | Account balances and movement history reconcile across canonical Ledger, Escrow, Witness, Idempotency, Audit, and Outbox; discrepancies fail closed. |
| `authority_boundary` | Authority matrix + negative tests | Exactly one authoritative value Ledger, Escrow state machine, witness path, and outbox path; prohibited writes are denied. |
| `core_correctness` | CORE contract and repeatable tests | Frozen CORE invariants pass against the exact revision, including no duplicate release or value movement. |
| `adapter_boundaries` | Adapter contract tests | Every layer crossing uses the declared adapter; invalid, missing, or unauthorized requests fail closed. |
| `eai_g3_governance` | EAI/G3 policy contract + tests | Trust, Transparency, Performance and governance conditions are explicit, machine-checked, and required before release. |
| `transaction_correctness` | PostgreSQL transaction evidence | Commit/rollback, concurrency, replay, conflicting idempotency, and single-release behavior verified in PostgreSQL. |
| `recovery` | Crash/restart/recovery evidence | Abandoned work is recovered safely; no duplicate movement; failed verification remains HOLD. |
| `auditability` | Witness/audit/outbox linkage report | Every committed value movement has matching witness, audit evidence, idempotency record, and correctly typed/aggregated outbox event. |
| `security_iam_mfa` | IAM/MFA and privileged-access evidence | Privileged identity, MFA enforcement, access review, least privilege, and revocation tested; policy documentation alone is insufficient. |
| `observability` | Runtime telemetry and alert evidence | Readiness/liveness, structured logs, metrics, tracing/correlation IDs, and actionable alerts are exercised. |
| `performance_stress` | Repeatable load/stress report | Defined throughput/latency/error thresholds and concurrency limits pass on a declared environment; raw results retained. |
| `disaster_recovery` | Backup/restore and recovery-time evidence | Restore from backup, integrity reconciliation, RPO/RTO measurement, and failover/recovery procedure successfully re-performed. |
| `ci_release_governance` | Branch protection/release pipeline evidence | Required checks, review/approval policy, artifact provenance, deployment authorization, and rollback controls are verified. |
| `independent_reperformance` | Independent reviewer execution record | A reviewer other than the implementation author reproduces the critical tests from a clean checkout/environment and records exact SHA/results. |
| `final_evidence_bundle` | Complete signed/indexed evidence bundle | All required artifacts are present, integrity-checked, traceable to the exact SHA, and no gate is inferred from unrelated test success. |

## Execution order

1. **Inventory and authority**: `inventory_map`, `error_duplicate_excess`, `authority_boundary`, `adapter_boundaries`.
2. **Canonical behavior**: `core_correctness`, `eai_g3_governance`, `transaction_correctness`, `cross_store_reconciliation`, `auditability`.
3. **Operational resilience**: `recovery`, `security_iam_mfa`, `observability`, `performance_stress`, `disaster_recovery`.
4. **Release assurance**: `ci_release_governance`, `independent_reperformance`, `final_evidence_bundle`.
5. Re-run the PostgreSQL evidence workflow and master gate for the same exact commit SHA. A later commit requires a new exact-SHA evidence run.

## Fail-closed rule

The workflow's `architecture-gates.json` must identify the exact target SHA and point each
successful gate to an artifact that actually exists in the downloaded evidence bundle, or to a
traceable external evidence URI. Missing, stale, mismatched, unrepeatable, or merely planned
evidence remains non-success.

**No production lock is authorized by this plan.** The lock decision remains controlled by the
master gate and its exact-SHA evidence.

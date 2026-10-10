# PRODUCTION READY — MASTER WORK PLAN v1.0

Status: LOCKED AS CONTROL PLAN / PRODUCTION NOT LOCKED
Locked: 2026-10-06
Repository: butnee-sys/gerchain
Scope: Fundamental Architecture + EAI (Escrow as Infrastructure)
Excluded until EAI is production-ready and locked: downstream product/application layers.

## 1. Purpose

This document is the controlling production-readiness plan. It defines the evidence gates required before the fundamental architecture and EAI can be declared production-ready.

This plan is not itself a production-readiness declaration.

## 2. Canonical sequence

CANONICAL ARCHITECTURE
→ INVENTORY/MAP
→ ERROR/DUPLICATE/EXCESS
→ RECONCILIATION
→ AUTHORITY
→ CORE
→ ADAPTER
→ EAI/G3
→ TRANSACTION CORRECTNESS
→ RECOVERY
→ AUDITABILITY
→ SECURITY/IAM/MFA
→ OBSERVABILITY
→ PERFORMANCE/STRESS
→ DR
→ CI/RELEASE
→ INDEPENDENT RE-PERFORMANCE
→ FINAL EVIDENCE
→ PRODUCTION LOCK

## 3. Non-negotiable production gates

A gate may be marked GREEN only from fresh, reproducible evidence at the exact evaluated commit.

1. Canonical architecture conformance.
2. Single authoritative value Ledger.
3. Single durable Escrow aggregate/state truth.
4. EAI/G3 condition and trust controls.
5. Decision → Authorization → Release.
6. Atomic value movement.
7. Durable idempotency and replay/conflict protection.
8. Witness and Outbox evidence binding.
9. Deep value-truth reconciliation.
10. Recovery without duplicate value movement.
11. Legacy value-authority write freeze.
12. Production PostgreSQL boot and runtime verification.
13. PostgreSQL migration serialization and checksum stability.
14. Security/IAM/MFA and privileged-access evidence.
15. Observability/readiness/health evidence.
16. Performance/stress evidence.
17. Disaster-recovery evidence.
18. CI/release evidence.
19. Independent re-performance.
20. Final evidence index and lock record.

## 4. Current verified blockers

### BLOCKER A — production runtime test collection

GitHub Actions run associated with commit e860f502f3e1a2d56fd873ad2faab7b1ab630740:
- core-gates: FAILURE
- PostgreSQL Concurrency: FAILURE

The core-gates job reported Python SyntaxError during test collection in services/gerchain_runtime.py. The current branch file must be revalidated at the exact branch head and the CI result must be regenerated; no GREEN claim is permitted from the failed run.

### BLOCKER B — PostgreSQL migration concurrency

PostgreSQL Concurrency run failed:
test_migrations_are_serialized_and_checksum_is_stable

Observed failure:
UniqueViolation on schema_version_pkey, version=2.

This is a genuine migration-concurrency correctness failure and must be fixed and re-run before production lock.

## 5. Required closure order

A. Reconcile exact branch head versus CI-tested SHA.
B. Eliminate runtime/test collection defect and obtain fresh core-gates success.
C. Fix migration serialization so concurrent migration attempts cannot insert duplicate schema versions.
D. Re-run PostgreSQL concurrency suite; require all tests passing.
E. Add/verify production PostgreSQL boot test against canonical runtime factory.
F. Execute canonical value-flow re-performance: CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, READ.
G. Execute deep value-truth reconciliation and recovery/replay/conflict matrix.
H. Verify legacy value authorities cannot mutate production truth.
I. Verify production entrypoint and readiness semantics.
J. Run security, performance, DR and release gates.
K. Perform independent re-performance.
L. Produce final evidence index.
M. Only then create a separate PRODUCTION LOCK record.

## 6. Lock rule

This plan remains immutable unless an explicit architecture/process change is approved.

Changing the plan does not close a technical gate.

Production status may be changed only by fresh evidence satisfying every mandatory gate.

## 7. Current decision

MASTER WORK PLAN v1.0: LOCKABLE / CONTROL PLAN LOCKED.

Production readiness: NOT LOCKED.

EA-35: IN PROGRESS / NOT LOCKED.

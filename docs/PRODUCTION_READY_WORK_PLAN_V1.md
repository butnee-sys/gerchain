# PRODUCTION READY WORK PLAN v1.0

Status: LOCK CANDIDATE
Repository: butnee-sys/gerchain
Working branch: feat/ea21-transaction-aware-ledger

## 1. CLOSED BASELINE — DO NOT REPEAT

The following are accepted as previously completed technical evidence and are not reopened unless new code changes directly invalidate them:

- PostgreSQL concurrency — GREEN.
- Core release atomicity / idempotency — GREEN.
- Abandoned PROCESSING recovery — GREEN.
- Operating reconciliation — GREEN.
- CORE reconciliation CI — GREEN.
- Witness integrity / tamper evidence — GREEN.
- DEE key management — GREEN.
- DEE security — GREEN.
- CodeQL — GREEN.
- PwC baseline — FROZEN.

Rule: historical failures already corrected are not new work items. No duplicate testing or duplicate validation is performed solely to repeat prior closure.

## 2. CURRENT PRODUCTION CLOSURE SCOPE

A. Canonical production runtime construction
- Production entrypoint must instantiate the actual ProductionRuntimeFactory contract.
- Canonical Ledger must be the only production value authority.
- Legacy value authorities remain non-authoritative and must fail closed.

B. Canonical persistence completeness
- Ledger accounts and movements.
- Durable Escrow aggregate and complete lifecycle states.
- Witness evidence.
- Transaction-participating Outbox.
- Durable Idempotency.
- Required constraints/indexes/uniqueness.

C. Cross-store value truth
- Movement ↔ Escrow ↔ Witness ↔ Outbox ↔ Idempotency.
- Integrity binding.
- No orphan/unwitnessed/unoutboxed committed value movement.
- State-only operations remain distinct from value movement.

D. Production transaction paths
- CREATE
- FUND
- LOCK
- RELEASE
- REFUND
- CANCEL
- SETTLEMENT
- READ
All production value movement must pass the Canonical Ledger boundary.

E. Recovery / restart
- Abandoned processing.
- Idempotent replay.
- No duplicate value movement.
- Recovery cannot create alternate truth authority.

F. Production deployment
- PostgreSQL-only production entrypoint.
- Docker/compose configuration.
- Startup/readiness semantics.
- Migration path.
- Fail-closed behavior.

G. Evidence and governance
- Exact-SHA CI evidence for current production branch.
- Independent re-performance.
- Resolve documentation baseline inconsistency.
- Organizational IAM/MFA and privileged-access evidence remain separate governance gates.

## 3. LOCK CRITERIA

Production Ready v1.0 may be locked only when all current-scope gates are evidenced:

1. Canonical authority proven.
2. Complete production schema proven.
3. All production transaction paths proven.
4. Deep value-truth reconciliation proven.
5. Recovery/replay proven.
6. Legacy value authorities frozen/non-authoritative.
7. Production entrypoint boot proven against PostgreSQL.
8. Deployment configuration proven.
9. Current-SHA CI evidence retained.
10. Independent re-performance completed or explicitly accepted as a separate governance gate.

No GREEN is declared from source inspection alone where runtime evidence is required.

## 4. NON-REOPEN RULE

Do not repeat:
- PostgreSQL concurrency testing already closed.
- Core-gates failure already corrected.
- Any other previously closed control, unless a subsequent code change materially invalidates its evidence.

A new test is justified only by:
(a) a changed implementation path,
(b) a newly discovered authority/boundary defect,
(c) a previously untested production requirement,
or (d) a required current-SHA release gate.

## 5. ARCHITECTURE INVARIANTS

- One authoritative Ledger.
- One authoritative Witness path.
- One production Outbox authority.
- No application-owned value truth.
- Decision → Authorization → Release.
- No direct release.
- No duplicate Escrow Engine.
- No alternate production value authority.
- Unknown/unresolved required condition => DENY/HOLD.
- Recovery never creates alternate truth.
- Value movement is atomic with required durable evidence.

## 6. FINAL STATE

CURRENT: IN PROGRESS / NOT LOCKED

Next work is limited to unresolved production closure gates, not historical re-validation.

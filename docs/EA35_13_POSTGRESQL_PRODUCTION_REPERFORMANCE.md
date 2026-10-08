# EA-35.13 — PostgreSQL Production Re-performance Gate

Status: **LOCKED — VERIFIED**

This evidence record defines the branch-tip production verification gate.

Required runtime construction:
- PostgreSQL database URL only.
- ProductionRuntimeFactory must apply the authoritative migration history.
- Production schema guard must pass.
- GerchainRuntime must attach the Canonical Ledger authority.
- Legacy ReleaseAccount / MoneyLedger / AccountBalance must not be the production value authority.

Required execution evidence:
1. Production runtime boot.
2. Canonical tables present.
3. Canonical Ledger account creation.
4. FUND value movement.
5. LOCK state transition.
6. RELEASE value movement.
7. RELEASE replay/idempotency.
8. REFUND with authoritative refund destination.
9. CANCEL with authoritative original sender.
10. SETTLEMENT through Canonical Ledger.
11. Deep Value Truth reconciliation after the flow.

A GitHub Actions PostgreSQL service is configured to execute this gate on the branch.

No GREEN or production lock is declared until a fresh branch-tip PostgreSQL run completes successfully and its exact commit SHA is recorded.


## Current-tip re-verification trigger — 2026-10-02

This section intentionally creates a new exact-SHA release evidence point after the production-runtime construction and schema-guard corrections.

Required fresh branch-tip gates:
- PostgreSQL production re-performance
- production-postgresql-gate
- Canonical EAI PostgreSQL Gate
- independent PostgreSQL evidence
- deep value-truth reconciliation

Historical successful runs are retained as historical evidence only. They do not certify this new execution SHA.

Decision rule: any failed canonical production gate remains an open blocker; queued is not PASS; only completed SUCCESS on the exact commit may be promoted to current execution evidence.

- Fresh verification request: 2026-10-02 exact-SHA execution.


## Fresh CI observation — 2026-10-04

The workflow associated with commit `e860f502f3e1a2d56fd873ad2faab7b1ab630740` executed PostgreSQL 16 successfully, but its `core-gates` job failed during test collection because the PR merge snapshot contained literal `\\n` sequences in `services/gerchain_runtime.py`. The current branch-tip file has no such escaped-newline sequences. This historical failure is therefore not treated as current production evidence. A fresh branch-tip execution is required before any gate can be promoted.

## Exact branch-tip execution trigger — 2026-10-04

A fresh branch-tip execution is being triggered after verification that the current `services/gerchain_runtime.py` contains no escaped-newline corruption and that `ProductionRuntimeFactory` applies migrations, validates the canonical schema, and attaches Canonical Ledger authority. This marker is evidence metadata only; it does not certify the resulting run.

## LOCK DECISION — 2026-10-07

Status: **LOCKED — VERIFIED**

Exact branch-tip commit:
- `c9ca958a88a8f7abb4ca95159bb214a1fb03cf8d`
- Commit: `docs(ea35): lock PostgreSQL production evidence`

Fresh exact-SHA evidence:
- `production-postgres` run **37555558755** — SUCCESS
- `production-postgresql-gate` run **37555558722** — SUCCESS
- `EAI PostgreSQL Production Proof` run **37555558737** — SUCCESS
- `independent-postgresql-evidence` run **37555558746** — SUCCESS

The verified gate covers PostgreSQL production boot, canonical schema/migration guard, Canonical Ledger authority, canonical value movement, replay/idempotency, lifecycle flows, settlement, and deep value-truth reconciliation through the configured production evidence workflows.

Decision:
**EA-35.13 PostgreSQL production re-performance gate is locked at exact SHA `c9ca958a88a8f7abb4ca95159bb214a1fb03cf8d`.**

Scope limitation:
This lock certifies the PostgreSQL production evidence gate only. It does not by itself certify the entire overall production architecture, security/IAM, observability, disaster recovery, performance/stress, or final production release lock.


EA-35.35 fresh PostgreSQL verification trigger: current branch contains the runtime syntax correction and conflict-safe migration publication path; CI must re-perform both gates before any production lock.

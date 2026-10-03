# EA-35.13 — PostgreSQL Production Re-performance Gate

Status: IN PROGRESS / NOT LOCKED

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

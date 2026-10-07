# EA-35 PostgreSQL Production Evidence

## Status
- Production PostgreSQL gate: **PASS**
- EAI production status: **VERIFIED**
- Overall architecture lock: **NOT YET LOCKED**
- Evidence correction commit: `6fdbce7d74aff21e084b616460247e8faed77f7f`
- Workflow runs: `37621992299` (EAI proof), `37621992207` (production PostgreSQL), `37621992236` (independent PostgreSQL evidence), `37621992149` (production gate)
- Job: `postgresql-production-gate`
- Verified: 2026-10-07 (fresh runs)

## Fresh PostgreSQL evidence

All steps in the production PostgreSQL gate completed successfully:

1. Python syntax gate — PASS
2. Production factory and canonical persistence — PASS
3. Production entrypoint boot against PostgreSQL — PASS
4. Deep value-truth reconciliation tests — PASS
5. EAI production re-performance — PASS
6. Real PostgreSQL production value-flow gate — PASS

Workflow job `postgresql-production-gate` completed successfully with all 11 execution steps PASS.

Runtime factory evidence:
- PRODUCTION_FACTORY_GATE=PASS
- CANONICAL_TABLES_GATE=PASS
- CANONICAL_LEDGER_MOVEMENT_GATE=PASS
- CANONICAL_LEDGER_REPLAY_GATE=PASS

Production entrypoint evidence:
- `GerChain production runtime initialized: escrow=ci-escrow-1 currency=USD`
- Controlled timeout after successful boot was accepted by the gate.

Test evidence:
- Deep reconciliation: 19 passed
- EAI production re-performance: 1 passed
- Real PostgreSQL production value-flow gate: 1 passed

## Authority proven

The fresh PostgreSQL gate proves, on the tested CI database:

- PostgreSQL is accepted as the production runtime database.
- ProductionRuntimeFactory establishes Canonical Ledger authority.
- Canonical ledger account creation works.
- Transaction-aware canonical movement works.
- Replay of the same transaction does not move value twice.
- Canonical persistence tables are present.
- Production entrypoint boots against PostgreSQL.
- Deep value-truth reconciliation passes.
- EAI re-performance passes across FUND, LOCK, RELEASE, REFUND, CANCEL and SETTLEMENT paths.
- Real PostgreSQL production value-flow integration passes across release, refund, cancel and settlement scenarios.

## Migration concurrency correction

The previous PostgreSQL concurrency evidence exposed a first-boot publication race on `schema_version(version=2)`. The migration runner was corrected to use transaction-scoped PostgreSQL advisory locking via `pg_advisory_xact_lock(73546501)`. The new production gate passed after this correction.

## Important boundary

This evidence is **repository/CI technical evidence**, not an external production certification or independent third-party attestation.

EA-35 production execution is **VERIFIED** on fresh exact-SHA CI evidence for `6fdbce7d74aff21e084b616460247e8faed77f7f`. EAI is production-ready within the tested scope. The overall canonical architecture remains **IN PROGRESS / NOT LOCKED** until security/IAM controls, privileged access governance, recovery/DR evidence, architecture-wide independent re-performance, and final lock criteria are closed.

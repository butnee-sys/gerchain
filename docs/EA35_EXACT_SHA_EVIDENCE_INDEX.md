# EA-35 — Exact-SHA Evidence Index

**Scope:** EAI / deep value-truth reconciliation / PostgreSQL production re-performance  
**Current audited SHA:** `e860f502f3e1a2d56fd873ad2faab7b1ab630740`  
**Branch:** `feat/ea21-transaction-aware-ledger`  
**Status:** IN PROGRESS / NOT LOCKED

| Evidence ID | Control | Exact evidence | Status |
|---|---|---|---|
| E-EA35-001 | Deep value-truth reconciliation | `persistence/deep_value_reconciliation.py` + `tests/persistence/test_deep_value_reconciliation.py` | IMPLEMENTED |
| E-EA35-002 | Operation-bound outbox evidence | movement operation ↔ escrow aggregate ↔ outbox event binding; negative mismatch test | IMPLEMENTED |
| E-EA35-003 | State-only LOCK separation | LOCK witness/outbox/idempotency can reconcile without a value movement | IMPLEMENTED |
| E-EA35-004 | Durable idempotency correctness | replay/conflict tests; state-only idempotency false-positive regression removed | IMPLEMENTED |
| E-EA35-005 | Canonical Ledger authority | production runtime configures `PostgreSQLAtomicLedger`; legacy value authorities are non-authoritative | IMPLEMENTED |
| E-EA35-006 | Production constructor correctness | `ProductionRuntimeFactory(ProductionRuntimeConfig(...)).create()` used by `production_entrypoint.py` | IMPLEMENTED at exact SHA |
| E-EA35-007 | PostgreSQL production gate definition | `.github/workflows/production-postgresql-gate.yml`; PostgreSQL 16 + boot + canonical tables + replay + value-flow + recovery + independent evidence | DEFINED |
| E-EA35-008 | Exact-SHA repository status | GitHub combined status for audited SHA: Snyk success | PARTIAL |
| E-EA35-009 | Fresh PostgreSQL execution result | Completed GitHub Actions run tied to audited SHA | UNVERIFIED |
| E-EA35-010 | Independent re-performance result | Fresh completed independent PostgreSQL evidence run tied to audited SHA | UNVERIFIED |
| E-EA35-011 | Exact-SHA evidence retention | workflow run ID, job result, logs/artifact retained for audited SHA | OPEN |

## Lock rule

EA-35 may be LOCKED only when E-EA35-009, E-EA35-010 and E-EA35-011 are machine-verifiable and tied to the same immutable audited SHA.

**No narrative PASS substitutes for a missing workflow result.**

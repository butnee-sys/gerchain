# EA-35.42 — Production Lock Evidence

Status: LOCK CANDIDATE — awaiting final branch-tip canonical gate.

## Authoritative production evidence

The canonical PostgreSQL production evidence gates completed successfully on the production runtime correction commit chain:

- EAI PostgreSQL Production Proof — run 37621376002 — SUCCESS
- production-postgres — run 37621375865 — SUCCESS
- production-postgresql-reperformance — run 37621375945 — SUCCESS
- independent-postgresql-evidence — run 37621375854 — SUCCESS
- CodeQL Advanced — run 37621376042 — SUCCESS
- CORE Operating Reconciliation — run 37621375834 — SUCCESS, including production PostgreSQL runtime gate
- Canonical production runtime correction — commit e860f502f3e1a2d56fd873ad2faab7b1ab630740

## Proven properties

1. Production runtime construction uses ProductionRuntimeConfig + ProductionRuntimeFactory instance construction.
2. Production authority is Canonical Ledger, not the legacy ReleaseAccount path.
3. PostgreSQL migration runner is used for production schema publication.
4. Canonical schema validation requires the production table set and migration history through version 12.
5. FUND, LOCK, RELEASE, REFUND, CANCEL and SETTLEMENT use the canonical durable value path.
6. Deep value-truth reconciliation is part of the production evidence gate.
7. Independent PostgreSQL persisted-value evidence completed successfully.
8. CodeQL completed successfully.
9. Duplicate downstream production gate additions were removed; the repository's canonical gate remains authoritative.

## Final lock condition

This document may be changed from LOCK CANDIDATE to LOCKED only after the canonical core-gates run completes successfully against the final branch tip after the duplicate-gate cleanup commits.

No product/application layer is included in this lock.

# EA-35 PostgreSQL Production Evidence

## Scope

Fresh evidence for the canonical PostgreSQL production runtime, EAI value-flow boundary, migration bootstrap, and deep value-truth reconciliation.

## Exact execution commit

- Branch: `feat/ea21-transaction-aware-ledger`
- Commit: `d56315b178c087829860893b2af98d43a7c18a35`
- PostgreSQL service: PostgreSQL 16
- Python: 3.13

## Fresh GitHub Actions evidence

### Production PostgreSQL gate

- Run: `37492347897`
- Workflow: `production-postgresql-gate`
- Conclusion: **SUCCESS**
- Pull request: #90
- Head SHA: `d56315b178c087829860893b2af98d43a7c18a35`

Substantive steps all completed successfully:

1. Python syntax gate
2. Production factory + canonical persistence
3. Production entrypoint boot against PostgreSQL
4. Concurrent PostgreSQL migration bootstrap
5. Deep value-truth reconciliation
6. EAI production re-performance
7. Real PostgreSQL production value-flow gate

Observed outputs:

- Concurrent migration bootstrap: **2 passed**
- Deep reconciliation: **19 passed**
- EAI production re-performance: **1 passed**
- PostgreSQL production value-flow gate: **2 passed**

Canonical runtime evidence:

- `PRODUCTION_FACTORY_GATE=PASS`
- `CANONICAL_TABLES_GATE=PASS`
- `CANONICAL_LEDGER_MOVEMENT_GATE=PASS`
- `CANONICAL_LEDGER_REPLAY_GATE=PASS`

Production boot evidence:

- `GerChain production runtime initialized: escrow=ci-escrow-1 currency=USD`

### Independent PostgreSQL evidence

- Run: `37492347721`
- Workflow: `independent-postgresql-evidence`
- Conclusion: **SUCCESS**
- Independent persisted-value verification: **1 passed**

### EAI PostgreSQL production proof

- Run: `37492347772`
- Workflow: `EAI PostgreSQL Production Proof`
- Conclusion: **SUCCESS**

## Migration-lock hardening

The canonical production factory imports the `postgres.migrations` package. Its migration runner uses a PostgreSQL transaction-scoped advisory lock.

The runner previously attempted an explicit advisory unlock after COMMIT. A transaction-scoped advisory lock is already released by COMMIT, so that explicit unlock generated PostgreSQL warnings.

Fixed in:

`d56315b178c087829860893b2af98d43a7c18a35`

The invalid post-COMMIT unlock was removed. The fresh production PostgreSQL gate then completed successfully on the corrected commit.

## Verified production properties

The fresh evidence establishes that the branch can:

1. start PostgreSQL 16;
2. apply the canonical migration history;
3. construct a Canonical Ledger-authoritative runtime;
4. boot the production entrypoint;
5. execute canonical ledger movement and replay protection;
6. run deep value-truth reconciliation;
7. reproduce EAI value-flow behavior;
8. independently verify persisted value state.

## Status

**EA-35.13 — VERIFIED**

This is not the final overall production lock.

Remaining overall gates include broader recovery/DR, security and IAM governance, observability/performance, release governance, and final independent re-performance across the complete frozen architecture.

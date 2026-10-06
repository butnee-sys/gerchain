# EA-34.11 — Production Runtime Value Authority Audit

Status: IN PROGRESS / NOT LOCKED
Branch: feat/ea21-transaction-aware-ledger

## Canonical production authority

Production value movement MUST use:
- Canonical Ledger accounts: gerchain_ledger_accounts
- Canonical Ledger movements: gerchain_ledger_movements
- Transaction-aware mutation: PostgreSQLAtomicLedger.transfer_in_transaction
- Canonical balance read: CanonicalLedgerRead

## Runtime cutover evidence

- FUND -> persistence.fund_escrow -> Canonical Ledger
- LOCK -> persistence.lock_escrow -> Canonical Escrow
- RELEASE -> persistence.release_escrow -> Canonical Ledger
- REFUND -> persistence.refund_escrow -> Canonical Ledger
- CANCEL -> persistence.cancel_escrow -> Canonical Ledger
- SETTLEMENT -> SettlementCoordinator -> Canonical Ledger
- CREATE ACCOUNT -> PostgreSQLAtomicLedger.create_account
- READ BALANCE -> CanonicalLedgerRead

## Legacy bypass findings

### API v1
api/v1.py previously performed direct SQLite escrow INSERT/UPDATE operations. These mutation endpoints are now fail-closed with HTTP 410 and explicitly direct callers to the production runtime boundary.

### Web UI
gerchain/web_ui.py previously mutated application-owned EscrowAccount.balance_nef directly. The legacy transfer mutation endpoint is now fail-closed with HTTP 410.

### In-memory / alternate runtime
network/api_server.py uses NEFStateEngine + TransactionManager in memory. This remains a non-production/legacy runtime and must not be the production entrypoint.

### CLI
node_cli.py uses NEFStateEngine + TransactionManager in memory. This remains a non-production/legacy runtime. Docker production entrypoint mismatch remains OPEN until replaced.

### SQLite stores
database/db.py and gerchain/database.py expose SQLite stores. They are not production value authority and remain legacy/alternate persistence surfaces until final removal/archive.

## Remaining hard checks

1. Production entrypoint must instantiate ProductionRuntimeFactory / canonical runtime.
2. No production path may instantiate MoneyLedger as value authority.
3. No production path may use ReleaseAccount or AccountBalance as balance authority.
4. No application-owned balance mutation may be reachable from production.
5. Canonical Escrow READ must come from durable PostgreSQL aggregate.
6. Movement-history reconciliation must include transaction_id, source, destination, amount, currency, operation, witness and outbox.
7. Legacy stores must be frozen read-only before removal/archive.
8. CI and independent re-performance evidence must be attached before lock.

## Current conclusion

EA-34.11 is NOT LOCKED. Direct legacy mutation surfaces identified above are now fail-closed, but production entrypoint, durable escrow READ, full movement reconciliation, legacy-store freeze/removal, CI evidence, and independent re-performance remain open.


## EA-35.13 verification update — 2026-09-27

### Exact PostgreSQL execution evidence

The production runtime/value-authority gate was executed against a real PostgreSQL 16 service on exact execution SHA `890a78f36dcfe161e195da649b3cd124133d6535`.

Successful workflow evidence includes:
- PostgreSQL production re-performance — run `36317914217`
- Production PostgreSQL Runtime — run `36317914351`
- production-postgres-smoke — run `36317914313`
- production-postgres-proof — run `36317914446`
- production-postgresql-gate — run `36317914344`
- PostgreSQL production verification — run `36317914254`
- EAI PostgreSQL Reperformance — run `36317914266`

All listed runs completed with conclusion `success`.

### Verified boundary

The exact execution verified:
1. PostgreSQL migration/schema initialization.
2. Canonical Ledger authority establishment.
3. Production entrypoint boot.
4. FUND / LOCK / RELEASE value-flow execution.
5. REFUND / CANCEL re-performance.
6. SETTLEMENT through the Canonical Ledger.
7. Durable replay/idempotency.
8. Deep value-truth reconciliation.
9. EAI PostgreSQL re-performance.

### Remaining closure gates

EA-34 / EA-35 is still **VERIFIED / NOT LOCKED** because:
- physical legacy-store removal/archive has not been independently closed;
- organizational IAM/MFA evidence remains a CORE assurance gap;
- branch/main governance evidence remains open;
- final independent oracle/re-performance package remains a separate assurance step;
- overall fundamental architecture lock requires reconciliation of these broader gates.

## EA-35.13 — Production PostgreSQL re-performance gate

Status: IN PROGRESS / NOT LOCKED

The production factory now applies the canonical PostgreSQL migration history and requires the canonical schema guard before constructing the runtime. The production entrypoint constructs `ProductionRuntimeConfig` and an instance of `ProductionRuntimeFactory`, then requires Canonical Ledger authority.

Required external evidence remains the GitHub Actions PostgreSQL re-performance gate on the exact branch tip. Local execution cannot substitute for that evidence in this environment because direct GitHub network access is unavailable.

Hard evidence requirements:
- PostgreSQL 16 service
- migration history reaches version 11
- canonical schema guard passes
- Canonical Ledger authority is established
- FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT execute against PostgreSQL
- deep value-truth reconciliation passes
- replay/idempotency remains single-movement

No production lock is declared until the exact branch-tip workflow evidence is retrieved and independently reviewed.

## EA-35.13 — Exact PostgreSQL re-performance evidence update — 2026-10-02

The branch produced exact GitHub Actions execution evidence for commit
`f158316277d65234e355b6040a905884ee4f4adf`.

Verified successful run:
- Workflow: `PostgreSQL production re-performance`
- Run: `37002917360`
- Job: `production-postgresql`
- Job conclusion: `success`
- PostgreSQL: 16.x service
- Python: 3.13.15
- Production re-performance test: **1 passed in 0.71s**

The successful test established:
1. Real PostgreSQL connectivity.
2. `ProductionRuntimeFactory` construction.
3. `production-postgresql` runtime mode.
4. `is_canonical_ledger_authoritative == True`.
5. Presence of the canonical runtime tables:
   - `gerchain_ledger_accounts`
   - `gerchain_ledger_movements`
   - `escrows`
   - `gerchain_transaction_witnesses`
   - `gerchain_outbox_events`
   - `gerchain_idempotency_records`

This is fresh **GREEN evidence for fresh PostgreSQL runtime construction**.

It is **not yet migration-upgrade evidence for an existing production database**. The current schema file is additive, but the production factory's `create_all()` path does not by itself perform arbitrary ALTER migrations against an already-existing legacy schema. Therefore the existing-database migration gate remains OPEN.

Current status:
**EA-35 — IN PROGRESS / NOT LOCKED.**


## EA-35.28 — Exact branch-tip production verification — 2026-10-06

Branch tip verified:
- Branch: `feat/ea21-transaction-aware-ledger`
- Exact commit: `f11fcb6411f1458c7bb4696566a695a52141b0c3`

Fresh GitHub Actions evidence attached to this exact commit:
- `production-postgres` — run `37463305181` — SUCCESS
- `production-postgresql-gate` — run `37463305107` — SUCCESS
- `EAI PostgreSQL Production Proof` — run `37463304934` — SUCCESS
- `independent-postgresql-evidence` — run `37463304855` — SUCCESS
- `CORE Operating Reconciliation` — run `37463305050` — SUCCESS
- `CodeQL Advanced` — run `37463304876` — SUCCESS

Production PostgreSQL job `112267996297` completed successfully through:
1. PostgreSQL migration and boot verification.
2. Production PostgreSQL value-flow verification.
3. Deep value-truth verification.

Production PostgreSQL gate job `112268002110` completed successfully through:
1. Exact evidence-commit recording.
2. Python syntax gate.
3. Canonical persistence verification.
4. Production entrypoint boot against PostgreSQL.
5. Deep reconciliation.
6. EAI production re-performance.
7. Real PostgreSQL production value-flow gate.

Independent persisted-value verification job `112267995003` also completed successfully.

### Evidence interpretation

The previous failed executions on 2026-09-27 are historical failure evidence, not current branch-tip failures. They exposed migration publication/checksum, environment wiring, transaction-binding and reconciliation-test defects; subsequent commits corrected those paths.

Current branch-tip PostgreSQL production evidence is therefore:
**VERIFIED — exact branch tip, real PostgreSQL, production runtime, value flow, deep reconciliation, EAI proof, and independent persisted-value verification.**

### Lock boundary

This evidence is sufficient to close the **EA-35 PostgreSQL production verification gate**.

It does not by itself close the broader fundamental-architecture lock. Remaining gates are:
- current `core-gates` run `37463305121` is still in progress;
- legacy value-store physical removal/archive;
- organizational IAM/MFA assurance;
- main-branch governance;
- final independent architecture/oracle package.

**EA-35 PostgreSQL gate: CLOSED / VERIFIED.**
**Overall fundamental architecture: NOT LOCKED.**

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


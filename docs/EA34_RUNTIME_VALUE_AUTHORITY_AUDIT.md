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


## EA-35.13 verification update — 2026-09-22

### Verified by source inspection

- `ProductionRuntimeFactory.create()` is an instance method; the production entrypoint now constructs `ProductionRuntimeConfig` and an explicit `ProductionRuntimeFactory` instance before calling `create()`.
- Factory initialization now attaches the canonical persistence metadata and calls `configure_canonical_ledger()`, followed by `require_canonical_ledger_authority()`.
- The production entrypoint independently asserts `runtime.is_canonical_ledger_authoritative`.
- Canonical schema migration `postgres/schema/002_canonical_production.sql` creates the Ledger, Witness, Outbox and Idempotency stores and extends the durable Escrow aggregate to the full lifecycle.

### Verification boundary

GitHub Actions has no workflow run associated with commit `68f0eb69a96fbd1369f1a8ea0570cc8f3f6af396` (`[]` returned). Therefore PostgreSQL execution is **not yet independently runtime-verified**. Source-level construction is corrected; production boot and end-to-end PostgreSQL execution remain OPEN.

Status remains: **IN PROGRESS / NOT LOCKED**.

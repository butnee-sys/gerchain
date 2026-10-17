# EA-34.1 — Production Runtime Value-Authority Dependency Map

Status: IN PROGRESS / NOT LOCKED

## Purpose

Map every runtime value read/write dependency before freezing legacy value stores.

## Current production-risk paths

| Path | Current implementation | Value authority | Target |
|---|---|---|---|
| GerchainRuntime.get_balance | MoneyLedger.get_balance | MoneyLedger | CanonicalLedgerRead |
| GerchainRuntime.create_account | MoneyLedger.create_account | MoneyLedger | Canonical Ledger account boundary |
| GerchainRuntime.create_hold | MoneyLedger.get_balance | MoneyLedger | CanonicalLedgerRead |
| GerchainRuntime.fund | AuthoritativeEscrowService → MoneyEngine → MoneyLedger | MoneyLedger | Canonical Ledger transaction |
| GerchainRuntime.refund | AuthoritativeEscrowService → MoneyEngine.atomic_settlement | MoneyLedger | Canonical Ledger transaction |
| GerchainRuntime.release (production mode) | PostgreSQLAtomicRelease | ReleaseAccount | Canonical Ledger transaction |
| Settlement legacy class | PostgreSQLAtomicSettlement | AccountBalance | SettlementCoordinator → Canonical Ledger |
| Web UI transfer/release | EscrowAccount.balance_nef mutation | Application-owned DB model | Deny as production value path |
| API v1 escrow action | direct SQL state mutation | legacy SQLite escrow table | Controlled adapter/runtime only |

## Authoritative target

Production value truth MUST be:

- balance: gerchain_ledger_accounts
- movement: gerchain_ledger_movements
- transaction-aware mutation: PostgreSQLAtomicLedger.transfer_in_transaction
- balance read: CanonicalLedgerRead
- settlement orchestration: SettlementCoordinator

## Legacy/non-authoritative stores

These must not mutate production value after cutover:

- MoneyLedger
- gerchain_release_accounts
- gerchain_account_balances
- application-owned EscrowAccount.balance_nef

They remain available only as migration/test/legacy evidence until EA-34+ reconciliation and independent re-performance are complete.

## Hard invariant

No production balance read or balance mutation may bypass the Canonical Ledger boundary.

## Cutover preconditions

1. Cross-store reconciliation has no unexplained mismatch.
2. Canonical Ledger account and movement schema is complete.
3. FUND, RELEASE, REFUND, CANCEL, and SETTLEMENT all use Canonical Ledger.
4. Runtime reads use CanonicalLedgerRead.
5. Legacy writes are frozen.
6. Production entrypoint does not instantiate an in-memory value authority.
7. Bypass APIs are removed, disabled, or routed through controlled adapters.
8. Recovery and outbox participate in the same transaction boundary.
9. CI and independent re-performance provide evidence.

## Important finding

ProductionRuntimeFactory currently configures PostgreSQL release only. It does not yet configure a complete production value-flow runtime. Therefore runtime_mode == production-postgresql MUST NOT be interpreted as proof that all value operations are PostgreSQL-authoritative.

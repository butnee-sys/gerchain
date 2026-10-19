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

## EA-35.13 production construction correction

The production factory was corrected on commit `e860f502f3e1a2d56fd873ad2faab7b1ab630740` to construct `ProductionRuntimeConfig`, initialize canonical persistence metadata, configure `GerchainRuntime` with `configure_canonical_ledger()`, and require Canonical Ledger authority.

`production_entrypoint.py` was corrected to instantiate `ProductionRuntimeFactory` with the real configuration object and call its instance `create()` method. The previous class-level call was incompatible with the factory's actual API.

This establishes the intended production construction path in source code. It is **not yet proof of production readiness**. Exact-SHA PostgreSQL execution evidence, deep reconciliation, recovery, and independent re-performance remain required before lock.

## Hard evidence rule

`runtime_mode == production-postgresql` alone is never treated as proof. Production lock requires fresh exact-SHA PostgreSQL gate evidence plus independent re-performance.


## Step 1 exact-candidate recheck — 2026-10-19

**Reviewed candidate before this evidence update:** `d38235d34744240afd9e3acdf2a1e196330126ad`.

### Current runtime authority path (repository inspection)

- `production_entrypoint.py` reads and validates the PostgreSQL URL and required runtime configuration, checks the SQLAlchemy engine dialect, constructs `ProductionRuntimeFactory`, verifies `is_canonical_ledger_authoritative`, and executes `SELECT 1` before returning the runtime.
- `services/gerchain_runtime_factory.py` owns `ProductionRuntimeConfig`, applies the explicit canonical PostgreSQL migration registry, checks canonical schema invariants, and configures `GerchainRuntime` with `configure_canonical_ledger(session_factory)`.
- Canonical value authority remains `gerchain_ledger_accounts` and `gerchain_ledger_movements`; production value movement must pass through the transaction-aware Canonical Ledger boundary.
- The migration registry declares the explicit canonical chain 001–017. This is source-level evidence only until clean PostgreSQL first-run and repeat-run execution is attached to the exact candidate.

### Exact-SHA CI observation

At the reviewed candidate SHA, the combined-status endpoint exposed only `security/snyk (butnee-sys): success`. The workflow-run lookup returned no PR-triggered runs for that SHA. Therefore the required fundamental-architecture/PostgreSQL CI result is **UNVERIFIED**, not PASS. Older PostgreSQL Concurrency failures observed on other SHAs are not evidence about this candidate and must not be silently reused as its result.

### Step 1 decision

**NOT COMPLETE — DO NOT START Step 2 yet.**

Architecture and runtime-authority source inspection is consistent with the canonical Ledger direction, but Step 1 cannot close until:
1. the authority map and frozen architecture are reviewed together at one exact candidate SHA;
2. the required exact-SHA fundamental-architecture/PostgreSQL workflow completes and its jobs are inspected;
3. any failures are repaired and the final candidate SHA is rechecked;
4. the evidence record is updated to that final tested SHA.

No production-ready or lock claim is made by this source inspection.

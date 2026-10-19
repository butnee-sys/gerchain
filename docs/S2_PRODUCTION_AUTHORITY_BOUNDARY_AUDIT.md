# S2 Production Authority Boundary Audit

Status: IN PROGRESS / NOT LOCKED  
Branch: `feat/ea21-transaction-aware-ledger`  
Scope: S2-01 legacy balance authority, S2-02 escrow truth, S2-03 outbox boundary, S2-04 runtime fallback.

## Verified from source

### S2-01 — Legacy balance authorities
- Canonical production balance and movement models are `gerchain_ledger_accounts` and `gerchain_ledger_movements` in `persistence/atomic_ledger.py`.
- Legacy balance authorities still exist in `persistence/atomic_release.py` (`ReleaseAccount`) and `persistence/atomic_settlement.py` (`AccountBalance`).
- Their classes and standalone mutation methods remain in the repository. This audit does not claim they have been physically removed or that every import/caller has been exhaustively enumerated.
- Production runtime factory configures Canonical Ledger, but legacy `release_postgres()` remains callable on `GerchainRuntime` after `configure_postgres_release()`. That is a residual legacy path requiring call-site audit/deprecation/fail-closed treatment.

### S2-02 — Escrow truth
- Canonical aggregate operations are routed through `persistence/escrow_aggregate.py` and the transaction-aware FUND/LOCK/RELEASE/REFUND/CANCEL functions.
- Legacy `ReleaseEscrow` remains declared in `persistence/atomic_release.py`; it is not evidence of canonical escrow truth, but its persistence model remains in the codebase.
- Production schema bootstrap applies versioned migrations and validates canonical escrow state constraints through `services/gerchain_runtime_factory.py`.
- Migration/backfill equivalence and historical data reconciliation are still separate release gates.

### S2-03 — Outbox
- Canonical value transactions use `persistence/transactional_outbox.py` to insert `OutboxEvent` within the caller-owned transaction.
- `persistence/recovery_outbox.py` also exposes `PostgreSQLOutbox.enqueue()`, which opens/commits its own transaction. This is acceptable only for post-commit delivery/event scheduling, not for the atomic canonical value-movement write path.
- One physical production table is intended: `gerchain_outbox_events`. The code still has more than one API for the same model; call-site inventory and proof that canonical mutations never use the standalone enqueue method remain open.

### S2-04 — Runtime memory fallback
- `GerchainRuntime` creates a `MoneyLedger` object even in production construction, but canonical-mode value methods should never use it.
- FUND previously fell through to `AuthoritativeEscrowService.fund()` when canonical authority was not configured. That could invoke in-memory movement in the legacy `production-postgresql` mode.
- Fixed: FUND now calls `_require_test_memory_fallback("FUND")` before using the memory implementation. Thus non-test runtime modes fail closed.
- Added regression test: `test_production_release_mode_cannot_fall_back_to_memory_fund`.

## Exact changes
- Runtime fix commit: `d80a912b411b367f7a668af3469b6f77d8fd5113`
- Regression test commit: `07a3876fc5698a799f7378b0fc23951304b03757`

## Verification status
- Source-level inspection: performed for the files listed above.
- The workflow-run lookup for test commit `07a3876fc5698a799f7378b0fc23951304b03757` returned no associated pull-request-triggered runs. This means CI is UNVERIFIED, not failed and not passed.
- No claim is made here that live PostgreSQL production re-performance has passed.

## Remaining gates
1. Enumerate all callers/imports of `ReleaseAccount`, `AccountBalance`, `ReleaseEscrow`, `ReleaseWitness`, and `PostgreSQLOutbox.enqueue()`; prove no production value path reaches them.
2. Add or verify tests that every runtime operation refuses memory fallback whenever runtime mode is not `test-memory`, including FUND, LOCK, RELEASE, REFUND, balance read, account creation, escrow read, and any remaining hold APIs.
3. Reconcile all historical escrow, balance, movement, witness, idempotency, and outbox rows before authority cutover.
4. Run the exact-SHA test suite and a real PostgreSQL migration/boot/operation/recovery/reconciliation test.
5. Keep production status IN PROGRESS / NOT LOCKED until fresh evidence is attached.

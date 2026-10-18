# GERCHAIN EAI — Consolidated Final-Lock Register

Status: **CONSOLIDATION COMPLETE / FINAL LOCK NOT YET AUTHORIZED**
Scope: **GERCHAIN EAI (Escrow as Infrastructure) and its required production foundation only**
Working branch: `feat/ea21-transaction-aware-ledger`
Latest reviewed correction: `e860f502f3e1a2d56fd873ad2faab7b1ab630740`

## 1. Scope boundary — frozen for this lock effort

- EAI means **Escrow as Infrastructure**. It is an architectural principle, not a new canonical layer, not G3 itself, not GerChain, and not a second Escrow Engine.
- G3 is the escrow foundation and governs escrow conditions/policy through Trust, Transparency, and Performance.
- GerChain provides the operational asset/value-flow infrastructure.
- Canonical Ledger remains the single authoritative production value store and movement boundary.
- **SHUUD is a fully isolated, independent standalone APP. It is unrelated to EAI and is excluded from this EAI lock scope, dependencies, gates, and completion calculation.**
- This document consolidates previously approved decisions. It does not reopen or silently change the frozen canonical architecture.

## 2. Frozen invariants

1. One canonical Ledger authority: `gerchain_ledger_accounts` and `gerchain_ledger_movements`.
2. No production value mutation outside the transaction-aware Canonical Ledger boundary.
3. One durable canonical Escrow state machine and one authoritative Escrow truth.
4. One authoritative Witness path; Witness is not interchangeable with Audit.
5. One authoritative production Outbox path.
6. Durable idempotency: exact replay is idempotent; same key with different request fingerprint conflicts.
7. Decision → Authorization → Release is mandatory; no direct release.
8. Trust, Transparency, and Performance are mandatory release conditions.
9. Unknown or unresolved required conditions fail closed.
10. Value mutation, Escrow transition, Witness, Outbox, and idempotency evidence must be transactionally consistent.
11. Recovery must not duplicate value movement. Failed verification remains HOLD.
12. Legacy/in-memory/SQLite value stores are non-authoritative and cannot silently become production fallbacks.
13. Balance equality alone is insufficient: movement/evidence graph must reconcile.
14. Production entrypoint must instantiate the Canonical Ledger runtime, not the legacy release-only runtime.

## 3. Consolidated implementation evidence

| Area | Evidence in repository | Current assessment |
|---|---|---|
| Canonical Ledger transaction-aware mutation | `persistence/atomic_ledger.py`, transaction-boundary tests | Implemented; exact-SHA CI/re-performance still required |
| Durable Escrow aggregate and state transitions | `persistence/escrow_aggregate.py`, FUND/LOCK/RELEASE/REFUND/CANCEL modules | Implemented path; complete production schema migration still open |
| FUND | `persistence/fund_escrow.py` | Runtime cutover implemented; PostgreSQL execution evidence open |
| LOCK | `persistence/lock_escrow.py` | Runtime cutover implemented; PostgreSQL execution evidence open |
| RELEASE | `persistence/release_escrow.py` | Runtime cutover implemented; verify authoritative beneficiary binding in final audit |
| REFUND | `persistence/refund_escrow.py` | Uses stored `refund_destination`, not caller-selected destination |
| CANCEL | `persistence/cancel_escrow.py` | CREATED state-only cancel and FUNDED reversal path implemented |
| SETTLEMENT | `persistence/settlement_coordinator.py` | Orchestrates canonical Ledger; no second balance authority intended |
| Balance/account boundary | `persistence/canonical_ledger_read.py`, `PostgreSQLAtomicLedger.create_account_in_transaction` | Implemented path; PostgreSQL execution evidence open |
| Cross-store reconciliation | `persistence/value_reconciliation.py` | Initial account reconciliation exists; not sufficient alone |
| Deep value-truth reconciliation | `persistence/deep_value_reconciliation.py`, `tests/persistence/test_deep_value_reconciliation.py` | Movement ↔ Escrow/Witness/Outbox/Idempotency/Integrity checks implemented; CI and live PostgreSQL re-performance open |
| Legacy mutation bypasses | `api/v1.py`, `gerchain/web_ui.py` | Identified legacy mutation routes fail closed with HTTP 410; verify with fresh tests |
| Legacy value authority freeze | `docs/EA34_LEGACY_VALUE_AUTHORITY_FREEZE.md` | Policy documented; physical removal/archive and runtime verification remain open |
| Runtime authority audit | `docs/EA34_RUNTIME_VALUE_AUTHORITY_AUDIT.md` | In progress; not a production lock certificate |
| Production entrypoint | `production_entrypoint.py`, `services/gerchain_runtime_factory.py` | Constructor/authority mismatch corrected in reviewed commit; real PostgreSQL boot remains unproven |

## 4. Production entrypoint correction

Reviewed commit: `e860f502f3e1a2d56fd873ad2faab7b1ab630740`.

The prior entrypoint called `ProductionRuntimeFactory.create(...)` as though it were a class/static constructor and wired the legacy PostgreSQL release-only authority, while checking for Canonical Ledger authority. This was inconsistent.

The correction constructs `ProductionRuntimeConfig`, instantiates `ProductionRuntimeFactory`, calls its instance `create()`, and configures the runtime through `configure_canonical_ledger()`. The factory initializes canonical persistence metadata rather than the legacy AtomicRelease schema.

This fixes the code-level construction mismatch only. SQLAlchemy metadata creation is **not** a substitute for versioned production schema migrations. Successful boot and transaction execution against a real PostgreSQL instance remain unverified.

## 5. Final-lock gates — remaining proof, not new architecture

- [ ] Exact branch-tip CI and relevant test results captured and reviewed.
- [ ] Versioned PostgreSQL migration creates the complete canonical schema, including full Escrow lifecycle, movement integrity fields, Witness, Outbox, and durable idempotency.
- [ ] Clean PostgreSQL boot through the Docker production entrypoint succeeds from an empty supported database.
- [ ] Production integration tests prove CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT/READ on the same canonical authority.
- [ ] Atomic rollback test proves no partial Ledger/Escrow/Witness/Outbox/Idempotency commit.
- [ ] Replay and conflicting-fingerprint tests prove idempotency under PostgreSQL.
- [ ] Deep reconciliation returns no issues on clean data and detects seeded corruption/orphans.
- [ ] Restart/abandoned-operation recovery proves no duplicate value movement; failed verification stays HOLD.
- [ ] Legacy stores and alternate entrypoints are proven unable to mutate production value or silently become authoritative.
- [ ] Beneficiary/release destination is bound to authoritative Escrow/policy state and cannot be caller-substituted without authorization.
- [ ] Security/IAM/MFA and privileged-access evidence gaps are closed or explicitly accepted by the authorized owner.
- [ ] Independent re-performance records exact commit, database version, migration version, commands, outputs, and reviewer.

## 6. Status interpretation

The repository includes substantial implementation and prior tests. However, the latest reviewed status response for the entrypoint correction showed only the Snyk security status as success; that is **not** evidence that the test suite or PostgreSQL production re-performance passed. A prior empty status result is not a pass.

Therefore this register does **not** claim 98% as a measured score, does not claim production-ready, and does not authorize FINAL LOCK. The remaining work is limited to collecting/closing the explicit proof gates above—not redesigning the architecture or bringing SHUUD into EAI.

## 7. Lock decision

**Current decision: NOT LOCKED — EVIDENCE GATES OPEN.**

Authorize FINAL LOCK only after the exact target commit passes the required checks and the production PostgreSQL re-performance evidence is attached to this register. Preserve all frozen architecture decisions unless a separately approved architecture-change proposal explicitly supersedes them.

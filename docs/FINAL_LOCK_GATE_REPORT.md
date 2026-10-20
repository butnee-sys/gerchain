# FINAL LOCK GATE REPORT — EAI / Canonical Production Runtime

**Status: FINAL LOCK HOLD — NOT PRODUCTION LOCKED**  
**Scope:** Fundamental architecture + EAI (Escrow as Infrastructure) + Canonical Ledger production runtime.  
**Excluded:** Product/application layers.  
**Prepared:** 2026-10-09  
**Working branch:** `feat/ea21-transaction-aware-ledger`

## 1. Decision

The FINAL LOCK process is initiated and the architecture invariants are reaffirmed. A production lock is **not** granted by this report. The repository evidence available at this checkpoint does not demonstrate a complete, successful PostgreSQL production re-performance, full exact-commit CI, recovery/restart proof, and independent re-performance. Calling the system production-locked without those artifacts would be an unsupported assurance claim.

Two distinct decisions must not be conflated:

- **Architecture freeze:** the canonical architecture is governed by `docs/DEE_ARCHITECTURE_FREEZE.md`; changes require an explicit architecture-change proposal and approval.
- **Production lock:** withheld until every mandatory gate below has a current, reproducible, exact-commit evidence artifact.

## 2. Non-negotiable invariants

1. One authoritative Canonical Ledger balance store and movement history.
2. No production fallback to in-memory `MoneyLedger`, `ReleaseAccount`, `AccountBalance`, or application-owned balance mutation.
3. Escrow lifecycle state is durable and authoritative in one canonical aggregate.
4. One authoritative Witness path; witness evidence must bind to the corresponding operation and value movement.
5. One authoritative transaction-participating Outbox path; operation type and aggregate must match the movement.
6. Durable idempotency: same key + same request replays; same key + different request conflicts.
7. Decision → Authorization → Release is mandatory; fail closed on unknown or unresolved required conditions.
8. Ledger movement, escrow transition, witness, outbox, and idempotency evidence must be transactionally consistent for each value-moving operation.
9. Recovery/replay must not duplicate value movement.
10. Deep reconciliation must prove the graph across movement, escrow, witness, outbox, idempotency, and integrity hash—not merely balance equality.
11. Production entrypoint must instantiate the canonical runtime and must not initialize legacy release authority as an alternate source of truth.
12. No new Escrow Engine, Ledger, Witness Chain, or architecture layer may be introduced to bypass these invariants.

## 3. Evidence checkpoint

| Gate | Current determination | Reason |
|---|---|---|
| Canonical architecture document | FROZEN baseline exists | `docs/DEE_ARCHITECTURE_FREEZE.md` is the governing architecture record |
| Production runtime constructor | Corrected in repository history | Entry point now constructs `ProductionRuntimeConfig` and calls the factory instance's `create()` |
| Canonical authority selection | Implemented in factory change | Factory configures Canonical Ledger authority instead of legacy PostgreSQL Release authority |
| Persistence metadata initialization | Implemented, not a migration proof | `metadata.create_all` is not a substitute for versioned production schema migrations |
| Exact-commit CI | INCOMPLETE / UNVERIFIED | The inspected status for commit `e860f502f3e1a2d56fd873ad2faab7b1ab630740` returned only a Snyk success status; this is not full test/CI evidence and does not prove the current branch tip is green |
| Real PostgreSQL boot + lifecycle re-performance | NOT EVIDENCED | No fresh run result/artifact supplied in the inspected evidence |
| Restart/recovery/no-duplicate proof | NOT EVIDENCED | Must be demonstrated against PostgreSQL, not inferred from unit tests |
| Full deep reconciliation on production-shaped data | NOT EVIDENCED | Unit-level reconciliation implementation is not equivalent to production re-performance |
| Independent re-performance | OPEN | Requires a reproducible run by a reviewer/operator independent of the implementation |
| Production lock | **WITHHELD** | Mandatory gates remain unproven |

## 4. Mandatory final-lock run

Run the following against a disposable, real PostgreSQL instance using the exact candidate commit and versioned migrations:

1. Record candidate commit SHA, clean checkout state, image digest, migration version, PostgreSQL version, and environment configuration with secrets redacted.
2. Apply migrations from an empty database; verify schema and constraints. Do not use `create_all` as the migration acceptance test.
3. Boot `production_entrypoint.py` with PostgreSQL URL and required escrow/currency/witness environment variables. Verify readiness and fail-closed behavior on invalid configuration.
4. Exercise CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, account creation, escrow read, and balance read through the canonical runtime.
5. Verify positive paths and adversarial paths: unknown state, wrong currency/amount, insufficient funds, denied authorization, failed Trinity condition, replay, changed-payload idempotency conflict, and competing concurrent operations.
6. Force transaction rollback at each write boundary; prove no partial ledger/escrow/witness/outbox/idempotency commit.
7. Restart the process and database connection between operations; recover abandoned work and prove no duplicate movement.
8. Run deep reconciliation; require zero issues and retain machine-readable report plus logs.
9. Run the complete repository test/security workflows on the exact candidate SHA. Preserve workflow URLs, job outcomes, test counts, and artifacts.
10. Have an independent reviewer reproduce the run from the recorded instructions and compare outputs.
11. Only then replace HOLD with a dated, exact-SHA production-lock decision. Any failed, missing, stale, or ambiguous evidence keeps the system on HOLD.

## 5. Lock policy

- Do not label the system GREEN or production-ready from implementation-only evidence.
- Do not treat a missing check/status as a pass.
- Do not silently relax any frozen invariant to obtain a green run.
- Do not remove legacy stores until reconciliation, read-only freeze, cutover verification, and rollback/recovery plans are evidenced.
- Do not begin product-layer work as a substitute for closing EAI and the fundamental architecture gates.

**Final disposition: ARCHITECTURE FREEZE RETAINED; PRODUCTION FINAL LOCK ON HOLD.**

# EA-35 Final Lock Readiness Record

**Status: IN PROGRESS / NOT LOCKED**  
**Purpose:** Prepare the canonical fundamental architecture + EAI for a defensible final production lock. This record is a gate ledger, not a lock declaration.

## Scope boundary

This release gate covers the canonical fundamental architecture and Escrow as Infrastructure (EAI). It does not authorize a final production claim for downstream products or application layers.

## Audited source baseline

- Repository: `butnee-sys/gerchain`
- Branch: `feat/ea21-transaction-aware-ledger`
- Audited head before this record: `923af266bd33601766ddbb216e7d42d2705dd10a`
- Production factory: `services/gerchain_runtime_factory.py`
- Production entrypoint: `production_entrypoint.py`
- Deep reconciliation: `persistence/deep_value_reconciliation.py`
- PostgreSQL migration runner: `postgres/migrations.py`
- PostgreSQL production smoke workflow: `.github/workflows/ea35-postgres-reperformance.yml`
- Exact-SHA full-suite workflow: `.github/workflows/final-exact-sha-full-suite.yml`
- Canonical fundamental gate: `.github/workflows/core-gates.yml`

Any change after the audited source baseline creates a new release candidate. All required checks must pass on the exact final commit, not merely on an ancestor.

## Source-level findings verified

1. The entrypoint constructs `ProductionRuntimeConfig`, instantiates `ProductionRuntimeFactory`, and calls its instance `create()` method.
2. The factory validates a PostgreSQL URL/engine, applies canonical PostgreSQL migrations, validates required canonical tables and schema history, configures the runtime with `configure_canonical_ledger()`, and requires canonical ledger authority.
3. The production smoke workflow provisions PostgreSQL 16, runs the value-truth tests, boots the production factory, and asserts canonical Ledger tables and authority.
4. A separate PostgreSQL value-truth workflow runs `tests/persistence/test_deep_value_reconciliation_postgres.py`.
5. The exact-SHA full-suite workflow runs the full pytest suite against a PostgreSQL service.
6. The canonical fundamental gate explicitly excludes SHUUD/application paths from the fundamental architecture gate.

These are source/workflow inspections, not proof that the workflows completed successfully.

## Exact-SHA execution evidence observed

At audit time, head `923af266bd33601766ddbb216e7d42d2705dd10a` had these GitHub Actions runs queued:

| Gate | Run ID | Observed state |
|---|---:|---|
| EA-35 PostgreSQL Re-performance | 38004328555 | QUEUED — no conclusion |
| EA-35 Value Truth PostgreSQL | 38004328442 | QUEUED — no conclusion |
| FINAL Exact-SHA Full Suite | 38004328483 | QUEUED — no conclusion |
| core-gates | 38004328435 | QUEUED — no conclusion |
| DEE Security Gate | 38004328452 | QUEUED — no conclusion |

The Snyk status context `security/snyk (butnee-sys)` was successful for that head. It is not a substitute for the PostgreSQL or full-suite gates.

Run URLs:
- https://github.com/butnee-sys/gerchain/actions/runs/38004328555
- https://github.com/butnee-sys/gerchain/actions/runs/38004328442
- https://github.com/butnee-sys/gerchain/actions/runs/38004328483
- https://github.com/butnee-sys/gerchain/actions/runs/38004328435
- https://github.com/butnee-sys/gerchain/actions/runs/38004328452

## Mandatory final-lock gates

A final lock is permitted only when all gates below have fresh evidence attached to the exact final candidate SHA.

- [ ] PostgreSQL production factory boot passes, including migration application and canonical schema assertions.
- [ ] Real PostgreSQL value-truth reconciliation passes; no SQLite-only result is accepted as PostgreSQL evidence.
- [ ] FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, account creation, and balance reads are verified against canonical durable authority.
- [ ] Atomicity/rollback, replay idempotency, fingerprint conflict, and no-double-movement recovery are demonstrated.
- [ ] Deep reconciliation reports no unexplained movement/witness/outbox/idempotency/integrity inconsistencies.
- [ ] Full exact-SHA test suite passes.
- [ ] Canonical fundamental architecture gate passes.
- [ ] Security gate passes and privileged-access/IAM/MFA evidence is reviewed separately; a code scan alone is not operational access assurance.
- [ ] Migration concurrency and duplicate-publication safety tests pass on PostgreSQL.
- [ ] Legacy value authorities remain non-authoritative and fail-closed production paths are verified.
- [ ] Independent re-performance records exact SHA, commands/workflows, results, and any deviations.
- [ ] Evidence index and lock-status documents are updated to the same final SHA.
- [ ] A final review confirms no unresolved mandatory gate and explicitly authorizes the lock.

## Decision rule

- A queued, missing, stale, skipped, or inconclusive check is **UNVERIFIED**, not PASS.
- A passing source-level test on SQLite does not replace PostgreSQL evidence.
- A passing CI run on an earlier SHA does not authorize locking a later SHA.
- If any mandatory gate fails or remains unverified, status stays **IN PROGRESS / NOT LOCKED**.
- Do not describe this readiness record itself as production certification, independent assurance, or final lock.

## Next action

Wait for the currently queued runs to complete, inspect their job steps and failure logs, fix any evidence-backed failure, then repeat the full required gate set on the new exact head. Only after that should the final lock decision be recorded.

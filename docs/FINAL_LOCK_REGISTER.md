# FINAL LOCK REGISTER — Foundational Architecture + EAI

Status: **FINAL LOCK IN PROGRESS — NOT LOCKED**
Scope: foundational architecture and EAI (Escrow as Infrastructure). CORE is one infrastructure/sub-infrastructure, not the entire scope. Product layers remain excluded until EAI is production-ready and locked.

## 1. Lock decision

This register opens the final-lock process and records current evidence. It does **not** declare production lock. No production-ready claim is valid until all mandatory gates below have fresh, reproducible evidence against one exact commit SHA.

## 2. Canonical invariants under lock review

- One authoritative production value ledger: `gerchain_ledger_accounts` + `gerchain_ledger_movements`.
- Production mutations use the transaction-aware Canonical Ledger boundary.
- Canonical Escrow, Witness, Idempotency and Outbox evidence must reconcile for every committed value movement.
- Decision → Authorization → Release remains mandatory; unresolved required conditions fail closed.
- Legacy/in-memory/SQLite balance stores are not production value authorities.
- No duplicate Escrow Engine, Ledger, Witness Chain, or Outbox authority.
- Recovery must not duplicate value movement.
- Trust, Transparency and Performance are mandatory release conditions.
- EAI is a principle/architecture commitment, not a new layer or duplicate engine.

## 3. Repository evidence recorded

Observed on branch `feat/ea21-transaction-aware-ledger`:

- `services/gerchain_runtime_factory.py` currently defines `ProductionRuntimeConfig`, applies the PostgreSQL migration registry, creates canonical ORM tables, and checks schema tables/columns/critical constraints at startup. Current file blob: `35c1be4eb005fea9eb424bb24d1a421629cc0a5d`.
- `production_entrypoint.py` currently validates PostgreSQL URL and required runtime identity, uses the factory instance constructor, requires canonical ledger authority, and disposes the engine on startup failure/shutdown. Current file blob: `47ca51c0d5b5e722170c2f8ba4761bf936bc7218`.
- `tests/services/test_production_entrypoint.py` includes unit tests for non-PostgreSQL rejection, required settings, instance factory construction, canonical authority and engine disposal. Current file blob: `082e457f9e3778dee62738bca753e375d22dc1f5`.
- `docs/EA34_RUNTIME_VALUE_AUTHORITY_AUDIT.md` records runtime value-authority cutovers and is explicitly IN PROGRESS / NOT LOCKED. Current file blob: `5c530b74e94b23496caa21f8ffafd900f241b01a`.
- `docs/EA34_LEGACY_VALUE_AUTHORITY_FREEZE.md` defines the Canonical Ledger as the sole production value authority and explicitly says legacy stores have not yet been physically frozen/removed. Current file blob: `a27ed134bd480f16c9cac545f81f876c613f06c7`.
- `persistence/deep_value_reconciliation.py` provides read-only cross-store checks for movement, escrow, witness, outbox, idempotency and integrity binding. Current file blob: `79ebb2c14169945e92fcccf72c8c72ab363b92e7`.

CI evidence checked for commit `e860f502f3e1a2d56fd873ad2faab7b1ab630740`: the combined status response contained Snyk success only. This does not establish unit-test, PostgreSQL integration, recovery, full CI or independent re-performance success for the current branch state.

## 4. Mandatory FINAL LOCK gates

| Gate | Required evidence | Current status |
|---|---|---|
| L-01 Exact source baseline | One exact commit SHA for the entire lock candidate; branch clean and no uncommitted changes | OPEN |
| L-02 Unit/regression CI | All required workflow jobs pass on that exact SHA | UNVERIFIED |
| L-03 Real PostgreSQL boot | Fresh PostgreSQL service, migrations applied, startup schema assertions pass | OPEN |
| L-04 Lifecycle integration | CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, account creation and reads tested against PostgreSQL | OPEN |
| L-05 Atomicity/idempotency | Commit, rollback, replay, conflict, concurrent execution and no-duplicate-movement tests pass | OPEN |
| L-06 Deep value-truth reconciliation | Clean graph matches; seeded missing/orphan/mismatch evidence is detected; actual production-like database returns no unexplained issues | OPEN |
| L-07 Crash/recovery/outbox | Restart, abandoned work, lease/recovery and delivery replay do not duplicate value movement | OPEN |
| L-08 Legacy authority isolation | All production routes fail closed; legacy stores cannot mutate production value truth; migration/freeze evidence exists | OPEN |
| L-09 Security/access governance | IAM, MFA, privileged access review and branch/release governance evidence is complete or explicitly risk-accepted | OPEN |
| L-10 Independent re-performance | Independent operator repeats critical tests from documented instructions and records results | OPEN |
| L-11 Final evidence bundle | Logs, workflow links, migration version, database configuration class, reports and exact SHA recorded | OPEN |
| L-12 Production lock approval | All required gates pass; unresolved risks have explicit owners and signed acceptance | BLOCKED |

## 5. Lock rules

1. No gate is GREEN based only on source inspection, mocked unit tests, or an unverified workflow response.
2. Any code change after the candidate SHA invalidates the lock candidate and requires the affected gates to be rerun.
3. Any unexplained reconciliation issue, failed integrity check, missing witness/outbox/idempotency evidence, or uncertain value authority blocks lock.
4. A failed startup/schema assertion is a safety control; it must not be bypassed to obtain a green boot.
5. This register may be updated with evidence, but the status remains NOT LOCKED until all required gates pass.

## 6. Next execution order

1. Pin the exact current branch head SHA and collect workflow status for that SHA.
2. Run the dedicated PostgreSQL integration workflow; inspect job logs and artifacts rather than relying on status labels alone.
3. Fix any failing tests/schema/migration issues on a new candidate SHA and rerun affected gates.
4. Execute lifecycle + deep reconciliation + crash/recovery checks against PostgreSQL.
5. Run independent re-performance.
6. Only then create a separate FINAL LOCK decision record referencing this register, exact SHA and evidence links.

**Current disposition: FINAL LOCK PROCESS OPENED; PRODUCTION FINAL LOCK DENIED PENDING EVIDENCE.**


## 7. Cumulative findings added to FINAL LOCK (2026-10-18)

This section updates the lock register from current source inspection. These are requirements to close through implementation and repeatable evidence—not reasons to stop at a “proof needed” statement.

### Current source anchors

- `services/gerchain_runtime_factory.py` blob: `126f51789101d60f9552cf4cc59af7cec78c3101`. It contains the explicit canonical migration invocation, model metadata setup, and fail-closed schema assertions.
- `production_entrypoint.py` blob: `7d466b715af03d982efbd41306959dc758bb0542`. It validates PostgreSQL configuration, constructs the factory instance, requires Canonical Ledger authority, tests database connectivity, and disposes the engine on failure/shutdown.
- `postgres/migrations/__init__.py` blob: `24c9578c8d697630e72f5121ff39aeb99a9f45a8`. It defines the ordered 17-file canonical migration chain and migration runner.
- `tests/services/test_production_entrypoint.py` blob: `c04a8d87b10a112d324f14edacc7de44c8f7f832`. It contains entrypoint-level regression tests; these do not substitute for running against a real PostgreSQL server.

### Newly explicit gates

| Gate | Requirement added to FINAL LOCK | Closure evidence required | Status |
|---|---|---|---|
| L-13 | **Migration registry integrity** — only the declared 17 canonical migration files are applied; missing, ambiguous, skipped, unexpected or checksum-drifted files fail closed | Clean database and supported upgrade-path runs; exact `schema_version` sequence 1–17; checksum history retained | OPEN |
| L-14 | **Database-enforced schema integrity** — required constraints must exist, have the expected semantic expressions, be validated, and include required NOT NULL / unique guarantees | PostgreSQL schema assertion output for clean install and upgrade; negative tests for weakened/rebound constraints | OPEN |
| L-15 | **Factory/entrypoint integration** — runtime factory, session factory and engine are the same PostgreSQL authority; no legacy Release authority is configured as the production value path | Exact-SHA automated test plus real PostgreSQL container boot and shutdown | OPEN |
| L-16 | **Container readiness contract** — successful process start alone is not readiness; readiness must imply migrations, schema assertions, connectivity and canonical authority succeeded | Container-level health/readiness test for success and failure modes | OPEN |
| L-17 | **Migration idempotency and concurrency** — repeated boot is safe and concurrent boot/migration attempts serialize without duplicate or partial schema history | Two-run and concurrent-start PostgreSQL tests, including injected migration failure and retry | OPEN |
| L-18 | **Schema history versus physical schema** — version rows cannot mask out-of-band DDL drift; boot rejects weakened constraints even when the migration ledger looks complete | Drift injection test followed by fail-closed boot; repair/re-run evidence | OPEN |

### Execution order updated

1. Add/retain regression tests for L-13 through L-18, including negative-path cases.
2. Run the canonical migration chain against a genuinely clean PostgreSQL database.
3. Run the same chain against a representative prior-version database and verify the resulting schema/history.
4. Run production-entrypoint/container boot and lifecycle integration tests against PostgreSQL.
5. Exercise failure, restart, concurrent migration, idempotency and deep-reconciliation scenarios.
6. Bind every result to one exact candidate SHA and retain job logs/artifacts.
7. Update gate statuses from observed outcomes; do not infer GREEN from code inspection or a successful static security scan.

**Register status remains: FINAL LOCK IN PROGRESS — NOT LOCKED.** The work continues by implementing and closing these accumulated gates; no product/application layer is brought into scope before the foundational architecture + EAI lock.

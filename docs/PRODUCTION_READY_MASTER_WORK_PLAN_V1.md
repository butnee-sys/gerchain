# PRODUCTION READY — MASTER WORK PLAN v1.0

**Document purpose:** Single authoritative closure plan for the FINAL LOCK of the fundamental architecture.
**Scope:** ҮНДСЭН БҮТЭЦ only.
**Disposition:** FINAL-LOCK CANDIDATE / BLOCKED — NOT LOCKED.
**Rule:** Do not reopen or repeat technical gates already supported by retained evidence unless a fresh exact-SHA check contradicts that evidence.

## 1. Frozen scope

This plan covers the fundamental architecture and its production-readiness gates. Product/application layers are outside this plan.

Canonical gate sequence remains frozen:

CANONICAL ARCHITECTURE → INVENTORY / MAP → ERROR / DUPLICATE / EXCESS → RECONCILIATION → AUTHORITY → CORE → ADAPTER → EAI / G3 → TRANSACTION CORRECTNESS → RECOVERY → AUDITABILITY → SECURITY / IAM / MFA → OBSERVABILITY → PERFORMANCE / STRESS → DR → CI / RELEASE → INDEPENDENT RE-PERFORMANCE → FINAL EVIDENCE → PRODUCTION LOCK.

The sequence is the architecture's control map, **not permission to reopen already-closed work**. Final-lock work is restricted to the evidence gaps below.

## 2. Existing technical evidence — retain, do not duplicate

- Canonical architecture freeze exists.
- Canonical production value authority is PostgreSQL Ledger accounts + movements.
- FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, account creation, and balance READ are implemented against canonical boundaries.
- Legacy API/Web UI mutation surfaces are fail-closed.
- Production entrypoint uses the production runtime factory and canonical Ledger authority path.
- A real PostgreSQL production verification passed on execution SHA `890a78f36dcfe161e195da649b3cd124133d6535`; retained workflow records include runs `36317914217`, `36317914351`, `36317914313`, `36317914446`, `36317914344`, `36317914254`, and `36317914266`.
- The production-entrypoint constructor correction `e860f502f3e1a2d56fd873ad2faab7b1ab630740` is an ancestor of that retained execution SHA.
- These are prior technical evidence, not a substitute for final exact-SHA lock evidence.

## 3. FINAL LOCK checklist — only remaining work

### FL-1 — Exact-SHA CI and production proof
**Status: BLOCKED / NOT VERIFIED.**
At evidence snapshot for audited SHA `e366596c9fedccb7c7f6d4df5eae32ab2a1a2940`, the combined status showed only `security/snyk` success. Required production/PostgreSQL, full-suite, EAI, security and independent-evidence jobs were queued with no conclusion. Queued is not PASS.
**Closure evidence:** all required checks complete successfully on one exact final-lock candidate SHA; retain run IDs, job summaries, logs and artifacts.

### FL-2 — Legacy-store authority disposition
**Status: OPEN.**
Legacy stores must be evidenced as physically frozen read-only, removed, or archived under an approved migration/disposition record. Do not repeat the completed runtime cutovers; verify only the remaining physical/operational disposition.
**Closure evidence:** migration/reconciliation result, no-write proof, retained archive/removal record, and no unexplained value discrepancy.

### FL-3 — Organizational identity and privileged-access assurance
**Status: MISSING.**
Required IAM/MFA enforcement and privileged-access inventory/review evidence is not established by source tests alone.
**Closure evidence:** retained policy/configuration evidence, MFA enforcement proof, privileged-account review and accountable approval.

### FL-4 — Repository/main-branch governance
**Status: UNVERIFIED.**
Main-branch protection/ruleset, required-review policy, and post-merge required-check evidence must be verified from repository administration and tied to the lock candidate.
**Closure evidence:** machine-verifiable ruleset/branch protection record and successful required checks on the candidate commit.

### FL-5 — Independent final re-performance and lock record
**Status: OPEN.**
Do not rerun completed technical work merely to create duplicate tasks. An independent reviewer/oracle must verify the retained exact-SHA PostgreSQL/value-truth evidence and the closures of FL-1 through FL-4.
**Closure evidence:** signed/attributed independent result, consolidated evidence index, explicit exceptions (if any) accepted by the responsible authority, and final immutable lock decision tied to a single SHA.

## 4. Required PostgreSQL and final-evidence execution gates

These gates are explicitly included in the FINAL LOCK work plan. They must be evaluated against the same exact candidate commit SHA; workflow configuration or a historical successful run is not itself proof.

### PG-1 — Clean PostgreSQL migration and schema verification
- Provision a fresh PostgreSQL database and apply the canonical migration chain from an empty state.
- Verify the migration registry has the expected contiguous versions and checksums.
- Re-run migrations and prove idempotency: no changed registry rows, checksums, timestamps, or constraints.
- Verify required tables, columns, indexes, foreign keys, check constraints, uniqueness constraints, and validated constraint status.
- Re-perform an upgrade path from the supported prior migration state and compare the resulting schema with the clean-install result.
- Preserve migration logs and schema/constraint snapshots as workflow artifacts.
**Closure evidence:** successful exact-SHA PostgreSQL workflow, clean-install and upgrade outputs, migration registry, schema/constraint comparison, and retained artifact references.

### PG-2 — Production entrypoint boot
- Start the production entrypoint against the freshly migrated PostgreSQL database using the production runtime factory.
- Assert the configured runtime reports Canonical Ledger authority; prove it does not initialize or fall back to legacy ReleaseAccount, in-memory MoneyLedger, SQLite, or other alternate value authority.
- Verify startup failure is fail-closed for missing configuration, non-PostgreSQL URLs, and schema/configuration errors.
- Capture process startup, readiness/health result, and clean SIGTERM/SIGINT shutdown evidence.
**Closure evidence:** exact-SHA logs and automated assertions showing successful PostgreSQL boot, canonical authority, negative startup cases, and clean shutdown.

### PG-3 — Full canonical escrow/value-flow re-performance
On PostgreSQL, exercise and verify:
1. CREATE — durable CREATED aggregate, no value movement.
2. FUND — source-to-escrow movement and CREATED→FUNDED.
3. LOCK — FUNDED→LOCKED, state-only, no ledger movement.
4. RELEASE — LOCKED→RELEASED, canonical Ledger movement.
5. REFUND — LOCKED→REFUNDED to the authoritative refund destination; caller-selected destination must not override it.
6. CANCEL — CREATED state-only cancellation and FUNDED cancellation with canonical reversal; invalid states fail closed.
7. SETTLEMENT — uses the same canonical Ledger authority, not a second balance store.
8. Account creation and balance/escrow READ — read the durable canonical records.
- Include idempotent replay, conflicting replay, insufficient balance, currency mismatch, concurrent operations, rollback/no-partial-write, and invalid-transition cases.
- Assert each value-moving operation commits exactly one consistent movement and its required escrow state, witness, outbox, and durable idempotency evidence.
**Closure evidence:** PostgreSQL integration-test results and persisted before/after balances, movements, escrow states, witness/outbox/idempotency records, including negative-case results.

### PG-4 — Deep Value Truth Reconciliation and recovery
- Run deep reconciliation over movement↔escrow↔witness↔outbox↔idempotency↔integrity bindings.
- Prove clean graph passes and deliberate corruption cases fail with actionable issue codes.
- Test transaction rollback and restart/abandoned-operation recovery; prove recovery cannot duplicate value movement.
- If verification fails during recovery, the operation remains held and is not promoted to authoritative truth.
**Closure evidence:** exact-SHA reconciliation report, injected-failure matrix, recovery logs, and proof of no duplicate movement.

### PG-5 — Exact-SHA CI, independent review, IAM/MFA
- Record the candidate commit SHA and verify every required CI job ran on that exact SHA; queued/pending/empty checks are UNVERIFIED, not PASS.
- Retain workflow/run IDs, job conclusions, logs, artifacts, and security scan output.
- Obtain an independent reviewer’s re-performance of the PostgreSQL migration, runtime boot, operation matrix, reconciliation, and recovery evidence.
- Attach organizational IAM/MFA evidence: privileged-account inventory and review, MFA enforcement proof, policy/configuration record, and accountable approval. Source tests alone cannot close this control.
- Verify main-branch protection, required reviews, and required status-check governance; preserve the machine-readable configuration evidence.
**Closure evidence:** exact-SHA CI evidence, attributed independent report, IAM/MFA approval evidence, and repository-governance record tied to the same lock candidate.

## 5. Decision rule

- No queued, pending, missing, or unverified item may be marked GREEN.
- A historical successful run does not prove a different SHA.
- A code commit does not prove organizational IAM/MFA or repository governance.
- Do not declare FINAL LOCK until FL-1 through FL-5 have evidence and the decision is tied to one immutable commit SHA.
- If an organizational control cannot be evidenced, the responsible authority must explicitly accept it as an exception; the implementation team must not silently waive it.

## 6. Current disposition

**ҮНДСЭН БҮТЭЦ — VERIFIED TECHNICAL BASELINE / FINAL LOCK BLOCKED / NOT LOCKED.**

Execution is limited to FL-1 through FL-5. All other work remains closed or frozen unless contradictory evidence is discovered. No product/application-layer work is included.


## 7. Mandatory next execution gate — three independent PostgreSQL proofs

These three proofs are added to the FINAL LOCK evidence package and must be executed against the same exact candidate SHA. They are not considered complete merely because the runner or reconciliation code exists.

### PG-CONC-01 — Concurrent migration-runner execution
- Start two independent processes/connections against the same clean PostgreSQL database and invoke the canonical migration runner concurrently.
- Assert the advisory transaction lock serializes the runs.
- Assert each migration version appears exactly once in `schema_version`, with the expected SHA-256 checksum.
- Assert neither process reports a checksum conflict, and a subsequent third run is a no-op.
- Retain both process outputs and SQL query results proving no duplicate version/checksum rows.
**Status: OPEN — current live PostgreSQL evidence not retained.**

### PG-SCHEMA-02 — Actual post-migration schema verification
- Apply all 17 migrations to a clean PostgreSQL database.
- Query PostgreSQL catalogs for the actual 17 migration versions and checksums, tables, columns, indexes, CHECK constraints, UNIQUE constraints, foreign keys, and applicable constraint validation status (`pg_constraint.convalidated`).
- Verify versions are complete and unique, checksums match the registered migration SQL, and a second migration run changes neither registry rows nor schema.
- Preserve raw catalog query output as an artifact tied to the candidate SHA.
**Status: OPEN — live PostgreSQL catalog output required.**

### PG-TRUTH-03 — Deep value-truth reconciliation on PostgreSQL
- Seed a clean canonical value-flow graph in PostgreSQL and call the real `deep_reconcile_value_truth(session)`.
- For every value movement, verify its escrow reference, operation/event binding, witness, outbox aggregate/event type, completed durable idempotency evidence, and recomputed integrity hash.
- Assert the clean graph passes; then inject individual defects (missing/mismatched witness, outbox, idempotency, escrow reference, and integrity hash) and assert reconciliation fails with the expected issue code.
- Retain the report and negative-test outputs from the actual PostgreSQL engine. SQLite-only results do not close this gate.
**Status: OPEN — live PostgreSQL reconciliation evidence required.**

### 7.4 Required evidence bundle

The three gates must publish: candidate SHA; PostgreSQL version; migration runner command; connection/process identifiers for concurrency; all 17 version/checksum rows; schema/constraint catalog dump; clean and corrupted reconciliation reports; workflow run/job IDs; logs and artifact references. Empty, queued, stale-SHA, mocked, or SQLite-only results are UNVERIFIED.

## 8. Progress percentage — scoring policy

The plan's total scope is normalized to **100%**, but a numerical completion percentage will only be published after assigning explicit weights to each master gate and scoring each gate from retained evidence. The current plan contains heterogeneous technical and organizational controls and does not define defensible weights; a guessed percentage would not be auditable.

Therefore the honest current reporting is:
- **Engineering implementation:** substantial; individual implemented controls remain evidence-scoped and are listed in the FINAL LOCK register.
- **Three requested PostgreSQL proof gates:** **0/3 closed (0% of this specific gate set)** until live PostgreSQL evidence is retained.
- **Platform-wide PRODUCTION READY FINAL LOCK:** **not issued; global lock closure remains 0%** because mandatory release sign-off gates remain open. This is a lock-decision metric, not a claim that no engineering work has been completed.

The master plan remains **FINAL-LOCK CANDIDATE / BLOCKED — NOT LOCKED** until evidence is collected and a weighted gate rubric is explicitly adopted.

## 5. Progress accounting and anti-duplication control (mandatory)

This plan is a FINAL-LOCK / EVIDENCE-CLOSURE plan, not a redesign, re-architecture, or rewrite plan. Design, canonical architecture, and implementation are prior work and must not be counted as newly remaining implementation tasks.

### 5.1 No percentage without a fixed denominator
- Never report a completion percentage unless it is calculated from a versioned, weighted checklist whose denominator and evidence references are retained.
- Do not change the denominator, weights, or completion rules between status snapshots without recording a formal revision and recalculating all snapshots consistently.
- A newly discovered issue does not automatically reduce completed work or increase the remaining-work percentage. First classify it as: (a) genuinely new defect, (b) already-known defect, (c) stale/duplicate alert, (d) environment/transient failure, or (e) evidence-only gap.
- The previously reported 70% complete / 30% remaining and 53% complete / 47% remaining are historical estimates only until their item-level denominators and weights are recovered and reconciled. They must not be treated as validated measurements or silently replaced by a new percentage.

### 5.2 Gate evidence is keyed by exact SHA + workflow run + job + conclusion
- A successful workflow on an exact SHA remains retained evidence for that SHA; do not reopen it because another workflow reports a similar gate name.
- A failure on the same SHA must be recorded separately with its exact run/job/failed step and classified before action. It does not erase unrelated successful evidence.
- Re-run a failed gate only when the failure is actionable and not already superseded by a successful run on the same SHA with equivalent or stronger coverage. If re-run is necessary, record why and compare the evidence rather than creating another duplicate task.
- A later commit is not automatically covered by evidence from an ancestor commit. For final lock, required checks must be tied to the exact final candidate SHA; inherited evidence can be reused only where code/configuration and coverage are demonstrably unchanged.

### 5.3 No repeated repair loop
For each confirmed defect, create one durable record with: defect ID, first evidence, root cause, fix commit, exact-SHA verification run, final disposition, and owner. Once verified, mark it CLOSED and link the evidence. Any recurrence must first be compared against that record; reopen only if a new exact-SHA result demonstrates a real regression.

### 5.4 Current evidence snapshot (2026-10-19)
The repository reports successful PostgreSQL production re-performance and runtime checks on execution SHA `890a78f36dcfe161e195da649b3cd124133d6535`, including runs `36317914217`, `36317914351`, `36317914313`, `36317914446`, `36317914344`, `36317914254`, and `36317914266`. The same SHA also has failed runs `36317914268` (PostgreSQL Concurrency: canonical production PostgreSQL value-truth gate) and `36317914284` (CORE Operating Reconciliation: operating reconciliation integration suite), while run `36317914283` (core-gates) and run `36317914237` (canonical-production-postgres) succeeded. These results are not interchangeable: inspect the failure logs and coverage before deciding whether the failed jobs are stale, flaky, or true gaps. Do not describe the whole SHA as universally green or universally failed based on a subset of runs.

**Progress percentage disposition: NOT RE-CERTIFIED.** No new percentage is asserted by this document. First reconcile the previous item-level scoring sheet against the fixed FINAL LOCK checklist and retained exact-SHA evidence; then publish one auditable percentage and remaining-work list.

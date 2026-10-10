# FINAL LOCK — Master Closure Sequence

Status: FINAL-LOCK PLAN / NOT LOCKED
Scope: Fundamental Architecture + EAI (Escrow as Infrastructure). Product layers remain out of scope until EAI is locked.

## Governing rule
Do not rerun a check already evidenced against the same immutable commit and unchanged artifact/configuration. Reuse exact-SHA evidence. Revalidate only if code, schema, configuration, runtime environment, threat model, or acceptance criteria changed, or if evidence is missing/stale/non-reproducible.

Evidence labels: VERIFIED (direct evidence tied to SHA/run/artifact); ACCEPTED BASELINE (frozen prior result, no rerun absent material change); OPEN; BLOCKED; LOCKED.

## 0. Freeze scope and build one evidence ledger
Record candidate commit/tree SHA, schema/migration version, deployment configuration fingerprint, scope, check ID, result, exact SHA, workflow/run ID, artifact/log, environment, and whether inputs changed. Reuse unchanged exact-SHA evidence. Do not create duplicate test items.

## 1. Canonical architecture conformance — delta review only
Reuse the frozen docs/DEE_ARCHITECTURE_FREEZE.md reference (freeze SHA 0940d8aae8858d34604eb9d7174a8afc636bb2f). Review only changes since freeze for adapter boundaries, single authoritative Ledger/Witness/Escrow path, Decision → Authorization → Release, fail-closed unknown conditions, idempotency and recovery. No full repeat architecture audit.

## 2. PostgreSQL evidence — verify applicability before rerun
docs/EA34_RUNTIME_VALUE_AUTHORITY_AUDIT.md records successful PostgreSQL 16 runs on SHA 890a78f36dcfe161e195da649b3cd124133d6535:
- 36317914217 — PostgreSQL production re-performance
- 36317914351 — Production PostgreSQL Runtime
- 36317914313 — production-postgres-smoke
- 36317914446 — production-postgres-proof
- 36317914344 — production-postgresql-gate
- 36317914254 — PostgreSQL production verification
- 36317914266 — EAI PostgreSQL Reperformance
Retrieve/verify logs and artifacts and compare tested code/schema/configuration to the candidate. Do not rerun if applicable and unchanged. If relevant changes exist after that SHA, run only affected gates on the candidate.
Required proof: migration/schema, boot, Canonical Ledger authority, FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT, replay/idempotency and deep reconciliation.

## 3. Production schema and fail-closed runtime
Confirm the candidate uses ProductionRuntimeConfig + ProductionRuntimeFactory instance construction, versioned migrations, schema-history assertion, Canonical Ledger authority, and fail-closed invalid configuration/schema. This is a delta check; rerun only if changed since applicable PostgreSQL evidence or evidence is insufficient. No create_all-only production initialization, hidden SQLite/memory fallback, or misleading readiness.

## 4. Deep value-truth reconciliation
Reuse EA-35 evidence tied to unchanged code. Ensure movement ↔ escrow ↔ witness ↔ outbox ↔ idempotency ↔ integrity hash coverage, including state-only LOCK and settlement. Run only missing/invalidated cases. Required exit: zero unexplained mismatches; reconciliation is read-only and fails closed on missing required evidence.

## 5. Legacy authority disposition
Reuse the EA-34.14 authority inventory; do not repeat the mapping audit. For ReleaseAccount, AccountBalance, ReleaseEscrow, ReleaseWitness, SettlementMovement, MoneyLedger and SQLite value stores, either prove production read-only/non-reachability and formally accept retention, or archive/remove via reviewed migration with before/after reconciliation. Never remove before movement reconciliation and backup/restore proof.

## 6. Governance and independent assurance
Close separately: IAM/privileged identity and MFA, privileged-access review, protected main-branch/required-check governance, independent re-performance/oracle package. Code tests do not prove organizational controls. Missing evidence remains OPEN unless formally risk-accepted by the accountable authority with scope, rationale, expiry/review date and residual risk.

## 7. Candidate-only CI and deployment proof
After code/schema/config are final, run required CI once on the exact candidate SHA. Every mandatory check must have a completed result; empty, pending, skipped without rationale, or evidence from an unrelated SHA is not PASS. On failure, fix the cause and rerun affected checks plus required downstream gates only.

## 8. Final lock manifest
Create docs/FINAL_LOCK_MANIFEST.md with architecture freeze reference, candidate commit/tree SHA, schema version, evidence ledger and run/artifact links, reused baseline evidence, newly executed checks, legacy disposition, governance decisions, independent sign-off, residual risks/exclusions, approver, UTC timestamp and immutable checksum. Do one consistency review of references; do not rerun the test suite.

## 9. FINAL LOCK decision
Lock only when every mandatory gate is closed, evidence is tied to the candidate or explicitly accepted as unchanged baseline, and no mandatory OPEN/BLOCKED item remains. Record FINAL LOCK: PASS or FINAL LOCK: BLOCKED, exact SHA, manifest checksum, scope (Fundamental Architecture + EAI), product-layer exclusion, and lock-reopening conditions. Missing proof means BLOCKED, not almost green.
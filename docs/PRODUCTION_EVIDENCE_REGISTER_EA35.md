# Production Evidence Register — EA-35.56

Status: IN PROGRESS / NOT LOCKED  
Branch: `feat/ea21-transaction-aware-ledger`  
Policy: FAIL-CLOSED. No criterion is PASS unless its verifier output is bound to the exact checked-out commit SHA and workflow run.

## Evidence rules

1. Every required criterion has a stable ID, executable verifier, result, evidence artifact, source SHA, and workflow run ID/attempt.
2. Aggregate workflow success does not imply that every criterion passed.
3. Missing, stale, malformed, or SHA-mismatched evidence is BLOCKED.
4. Migration source inventory and applied history must agree on version, canonical filename, and checksum.
5. Migration re-performance must run against a clean PostgreSQL database and a second time against the same database; the second pass must be a no-op with unchanged history.
6. Concurrent migration publication must be tested by multiple independent connections; exactly one row per canonical version must remain, with no checksum drift.
7. The schema catalog check must verify required tables, columns, unique keys, state constraint, and constraint validation.
8. A real production-entrypoint boot must use PostgreSQL and prove canonical Ledger authority. Mocked entrypoint tests are useful unit tests but do not count as PostgreSQL boot evidence.
9. The deep value-truth reconciliation must run against the migrated PostgreSQL database and return no issues for the seeded transaction graph.
10. The evidence bundle itself must have verified SHA-256 checksums.

## Canonical migration inventory

The runner in `postgres/migrations/__init__.py` explicitly declares this 17-version chain:

| Version | Canonical file |
|---:|---|
| 1 | `001_canonical_production.sql` |
| 2 | `002_canonical_production.sql` |
| 3 | `003_canonical_compatibility.sql` |
| 4 | `004_canonical_value_truth.sql` |
| 5 | `005_canonical_production.sql` |
| 6 | `006_canonical_movement_integrity.sql` |
| 7 | `007_canonical_production_reconciliation.sql` |
| 8 | `008_ea35_idempotency_compat.sql` |
| 9 | `009_canonical_movement_integrity_hardening.sql` |
| 10 | `010_canonical_evidence_constraints.sql` |
| 11 | `011_ea35_canonical_schema_finalization.sql` |
| 12 | `012_canonical_production.sql` |
| 13 | `013_ea35_canonical_schema_hardening.sql` |
| 14 | `014_canonical_escrow_state_constraint.sql` |
| 15 | `015_repair_escrow_state_constraint_drift.sql` |
| 16 | `016_reconcile_escrow_state_constraint.sql` |
| 17 | `017_ea35_created_witness_event.sql` |

This is a source inventory, **not proof that a database has applied those migrations**. Applied history must be collected from PostgreSQL `schema_version` and compared with freshly computed source checksums.

## Required per-criterion evidence schema

Each criterion record must include:

- `id`
- `status`: PASS, FAIL, or BLOCKED
- `source_sha`
- `checked_out_sha`
- `workflow_run_id`
- `workflow_run_attempt`
- `verifier`
- `evidence_artifact`
- `evidence_sha256`
- `result_summary`
- `failure_reason` (required unless PASS)

A record is eligible for PASS only if source_sha equals checked_out_sha, the workflow run is completed, the verifier actually ran, the artifact exists and its checksum verifies, and the criterion-specific assertion succeeded.

## Known gate behavior at register creation

The current `.github/workflows/production-gate.yml` creates a master decision whose per-criterion statuses are all hardcoded to BLOCKED with the reason that exact-SHA per-criterion verifiers are not wired. It then deliberately exits non-zero unless the overall status is PASS and lock authorization is true. Therefore, the current workflow is a fail-closed blocker, not a route to production lock. Do not weaken this behavior by hardcoding PASS or inferring PASS from aggregate job success.

The workflow's evidence-finalization step also assumes both migration artifacts already exist even when earlier steps failed. This should be hardened so missing artifacts are represented as explicit BLOCKED evidence, rather than masking the original failure with a secondary file-read exception.

## Current decision

**BLOCKED — NOT PRODUCTION READY — NOT LOCKED.**

Reason: source inventory exists, but this document itself contains no run-generated applied-history, exact-SHA test results, PostgreSQL re-performance results, or independent re-performance. No production-lock claim is authorized.

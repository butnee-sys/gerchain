# Production Migration Gate — Re-performance Protocol

**Status: OPEN / NOT LOCKED**  
**Scope:** Canonical PostgreSQL migration chain + production entrypoint + deep value-truth reconciliation.  
**Rule:** A successful local/unit test, ORM `create_all`, or documentation review is not proof that the production migration gate is closed.

## Canonical migration chain

The migration runner in `postgres/migrations/__init__.py` explicitly registers 17 canonical migration files (versions 001–017). It serializes concurrent runners with a PostgreSQL advisory lock, records SHA-256 checksums in `schema_version`, and fails closed on checksum drift or missing/ambiguous version files.

The authoritative chain is:
1. `001_canonical_production.sql`
2. `002_canonical_production.sql`
3. `003_canonical_compatibility.sql`
4. `004_canonical_value_truth.sql`
5. `005_canonical_production.sql`
6. `006_canonical_movement_integrity.sql`
7. `007_canonical_production_reconciliation.sql`
8. `008_ea35_idempotency_compat.sql`
9. `009_canonical_movement_integrity_hardening.sql`
10. `010_canonical_evidence_constraints.sql`
11. `011_ea35_canonical_schema_finalization.sql`
12. `012_canonical_production.sql`
13. `013_ea35_canonical_schema_hardening.sql`
14. `014_canonical_escrow_state_constraint.sql`
15. `015_repair_escrow_state_constraint_drift.sql`
16. `016_reconcile_escrow_state_constraint.sql`
17. `017_ea35_created_witness_event.sql`

## Required re-performance

Run against a newly created, disposable PostgreSQL database, with the exact candidate commit SHA recorded before execution.

1. Start PostgreSQL with a clean, empty database. Record server version and database identity.
2. Set `GERCHAIN_DATABASE_URL`, `GERCHAIN_ESCROW_ID`, positive integer `GERCHAIN_ESCROW_AMOUNT`, `GERCHAIN_CURRENCY`, and `GERCHAIN_WITNESS_ID`.
3. Run the migration runner through `ProductionRuntimeFactory` / `production_entrypoint.py`; do not pre-create tables manually.
4. Assert that `schema_version` contains exactly canonical versions 1–17, with checksums matching the checked-in files.
5. Query PostgreSQL catalogs and assert the canonical Ledger, Escrow, Witness, Idempotency, and Outbox tables and their required constraints/indexes exist.
6. Run production-path integration checks for CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, and READ against PostgreSQL.
7. Verify replay idempotency, conflicting-fingerprint rejection, rollback atomicity, concurrent movement behavior, and restart/recovery behavior.
8. Run `deep_reconcile_value_truth(session)`; require `report.matched is True` for a clean valid fixture and prove negative fixtures are rejected.
9. Stop and restart the runtime against the same database; verify no duplicate value movement and no loss of durable evidence.
10. Capture the CI run URL, job logs, migration-version/checksum output, catalog/schema assertions, test summary, reconciliation report, and exact commit SHA in one evidence bundle.

## Pass criteria

- All 17 migrations apply from an empty database in canonical order.
- A second migration run is idempotent and applies no new versions.
- A modified recorded migration checksum fails closed.
- Runtime boot establishes Canonical Ledger authority and refuses non-PostgreSQL URLs.
- All value-moving operations use the Canonical Ledger transaction boundary.
- Replay does not duplicate value movement; conflicting reuse is rejected.
- Rollback leaves no partial Ledger/Escrow/Witness/Outbox/Idempotency state.
- Deep reconciliation detects missing, mismatched, orphaned, or integrity-invalid evidence.
- Restart/recovery passes against PostgreSQL.
- Every result is tied to the exact candidate SHA and independently repeatable.

## Evidence record

| Evidence item | Required value |
|---|---|
| Candidate commit SHA | Pending |
| Clean PostgreSQL version/database | Pending |
| Applied migration versions | Pending |
| Migration checksums verified | Pending |
| Second-run idempotency | Pending |
| Production entrypoint boot | Pending |
| Runtime operation matrix | Pending |
| Replay/rollback/concurrency/recovery | Pending |
| Deep reconciliation | Pending |
| CI run URL and job logs | Pending |
| Independent re-performance | Pending |

## Lock rule

Until every required evidence item is recorded and independently checked, the gate remains **OPEN / NOT LOCKED**. Do not label production-ready or infer success from source-code presence alone.

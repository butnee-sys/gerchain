# EA-35.13 — PostgreSQL Production Re-performance Gate

Status: IN PROGRESS / NOT LOCKED

This gate is evidence-driven. No production-ready or GREEN claim is permitted until every required check passes on the same exact commit SHA.

## Required checks

### 1. schema_version history
- Exactly one row per version.
- Versions are contiguous from 1 through 13.
- Every checksum is non-empty and accepted by the frozen migration contract.
- A second complete migration pass leaves both version rows and checksums unchanged.

### 2. PostgreSQL migration concurrency
- Use two distinct PostgreSQL backend PIDs and two independent connections against one newly created empty database.
- Both migration calls must complete without exception.
- No duplicate schema_version rows may be published.
- Confirm the final version history is exactly 1..13.
- Rerun migrations and confirm checksums are unchanged.

### 3. Production boot
- Start against a real PostgreSQL service using the production entrypoint and required environment variables.
- Verify all canonical production tables exist after the approved migration path.
- Verify the runtime is configured with Canonical Ledger authority.
- Verify boot fails closed for a non-PostgreSQL URL, missing required configuration, or incomplete schema.
- SQLAlchemy metadata create_all is not a substitute for versioned production migrations.

### 4. Deep value-truth reconciliation
- Every canonical value movement must link to its authoritative escrow aggregate.
- Every value movement must have matching witness evidence, outbox event type and aggregate, completed durable idempotency evidence, and valid integrity hash.
- Reverse evidence checks must detect orphan witness/outbox records without falsely rejecting valid state-only operations such as LOCK.
- Reconciliation must be read-only and report all issues; any issue means the gate fails.

## Known historical CI evidence
A PostgreSQL Concurrency run failed with:
`UniqueViolation: duplicate key value violates unique constraint "schema_version_pkey"; Key (version)=(2) already exists.`
The failing log showed a plain INSERT. The current migration source includes `ON CONFLICT (version) DO NOTHING`, but that source change is not considered verified until a fresh exact-SHA run passes.

## Release decision
- A historical run is not evidence for a later SHA.
- Missing checks or workflow runs are UNVERIFIED, not PASS.
- Any failed check blocks production lock.
- Final evidence must record exact commit SHA, workflow/run IDs, test outcomes, and PostgreSQL version.

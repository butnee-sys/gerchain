# EA-35 — Production gate evidence ledger

Status: IN PROGRESS / NOT LOCKED

## Scope

This gate validates the fundamental canonical architecture and EAI persistence boundary. Product-layer work is out of scope until the foundational architecture and EAI are production-ready and formally locked.

## Step 2 — Error, duplicate authority, and excess-path audit

### Historical evidence reviewed

A PostgreSQL Concurrency workflow run (run ID 36542458201, job ID 117550062477) failed during a historical branch revision. Its PostgreSQL logs showed duplicate publication of `schema_version.version = 2` and a state-check rejection for `NOT_A_STATE`. This is evidence of a historical migration-publication race and expected fail-closed state constraint behavior; it is not evidence that the current branch passes.

A core-gates workflow run (run ID 36542458205, job ID 114820010500) failed during test collection because `services/gerchain_runtime.py` contained a literal escaped newline sequence in the `fund` method, producing a SyntaxError. The current branch source was subsequently inspected and the `fund` method is now represented as ordinary Python lines. The historical failure must be superseded by a fresh exact-commit run before the gate can be considered passed.

### Current source controls inspected

- Production factory uses the canonical PostgreSQL migration registry and then checks canonical schema invariants.
- Runtime factory configures the Canonical Ledger authority rather than the legacy PostgreSQL release authority.
- Production entrypoint requires a PostgreSQL URL, positive escrow amount, required configuration, a canonical runtime authority, and a successful database connection before returning the runtime.
- Legacy value authorities remain documented as non-authoritative. This document does not claim legacy tables have already been physically removed or made read-only.

### Step 2 acceptance criteria

1. Fresh exact-commit PostgreSQL concurrency regression passes.
2. Fresh exact-commit canonical architecture gate passes.
3. Fresh exact-commit full repository test suite passes.
4. Migration inventory/history audit passes on a clean PostgreSQL database.
5. No unresolved duplicate authoritative Ledger, Escrow, Witness, Outbox, or application-owned value-mutation path remains.
6. Production runtime boot proves canonical schema constraints and canonical Ledger authority.

Status: OPEN pending fresh exact-commit execution evidence and completion of the remaining authority-path audit.

## Step 3 — Deep value-truth reconciliation

The reconciliation contract requires each value movement to bind to its canonical escrow where applicable, the same transaction's witness, the matching outbox event, completed idempotency evidence, and a recomputable integrity hash. Settlement is treated as a value movement with its own explicit evidence binding; state-only operations must not be falsely required to have a ledger movement.

Required negative cases include missing/mismatched witness, missing or wrong-type outbox, missing/incomplete idempotency, missing/mismatched integrity hash, orphan escrow reference, and duplicate or conflicting migration history.

Acceptance requires a clean PostgreSQL run of the reconciliation suite, a clean report for the seeded canonical graph, and proof that every injected inconsistency is detected. Balance equality alone is insufficient.

Status: OPEN. Do not declare production readiness or lock the architecture until Step 2 acceptance is met and Step 3 passes on the same exact commit.

## Evidence integrity rule

A historical successful workflow, a source inspection, or a local/SQLite test is not a substitute for fresh PostgreSQL evidence tied to the exact commit under review. Missing workflow evidence means UNVERIFIED, not GREEN.

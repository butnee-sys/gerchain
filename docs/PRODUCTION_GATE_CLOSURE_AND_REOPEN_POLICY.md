# Production Gate Closure and Reopening Policy

Status: MANDATORY CONTROL
Applies to: Canonical Architecture, EAI, Canonical Ledger, production entrypoint, PostgreSQL migrations, deep value-truth reconciliation, security, recovery, release and deployment gates.

## 1. A green label is not a closure

A gate is CLOSED only when all required evidence is attached to the exact candidate commit and all acceptance criteria below pass. A green test run, a local test, a passing subset, a stale workflow run, or an implementation commit alone is not closure evidence.

Every gate record MUST contain:
- gate ID and immutable acceptance criteria;
- exact full Git commit SHA tested;
- workflow/run URL and attempt number;
- test command and environment identity (including PostgreSQL major version and migration revision where relevant);
- result summary, failed/skipped/xfail counts, and artifact links;
- required invariant checks and their output;
- independent re-performance evidence where the gate requires it;
- reviewer/approver and timestamp;
- explicit residual-risk disposition, if any.

Missing fields mean NOT VERIFIED, never PASS.

## 2. Evidence freshness and exact-SHA rule

1. Evidence applies only to the exact SHA tested.
2. Any code, migration, workflow, configuration, schema, entrypoint, or test change affecting a gate invalidates that gate's closure until the affected checks are rerun on the new SHA.
3. A branch name, PR head that later moved, successful run on an ancestor commit, cached local output, or an empty/missing status-check list is not evidence of success.
4. Required workflows must be present, triggered, completed, and successful. Pending, skipped, cancelled, unavailable, or absent required checks are NOT VERIFIED.
5. Tests must fail on assertion failures and must not silently skip required PostgreSQL tests when the required service/URL is unavailable.
6. CI evidence must include the exact commit SHA in its run metadata or artifact. If the run cannot be bound to the SHA, it cannot close the gate.

## 3. Production PostgreSQL gate

The production-readiness gate remains OPEN until a clean PostgreSQL environment proves all of the following on the same candidate SHA:
- canonical migrations apply from an empty database in deterministic order;
- a second migration run is idempotent and leaves migration history unchanged;
- schema/version checksums and required constraints match the repository's canonical migration chain;
- production entrypoint boots using the canonical runtime factory and fails closed for invalid URL, missing configuration, schema drift, missing/invalid constraints, and unavailable database;
- all required lifecycle and value-flow tests pass against PostgreSQL, not SQLite substitutes;
- RELEASE, REFUND, funded CANCEL, and SETTLEMENT each preserve atomicity, idempotency and one canonical movement;
- CREATED cancellation and LOCK remain state-only operations with no value movement;
- restart/recovery does not duplicate value movement;
- deep value-truth reconciliation returns matched for the clean fixture and detects seeded corruption in movement, escrow, witness, outbox, idempotency and integrity evidence;
- the migration and runtime use the same schema/table names and constraints;
- test output proves no required PostgreSQL test was skipped.

A schema create_all result, SQLite unit test, mocked engine, SELECT 1, or runtime object construction is insufficient by itself.

## 4. Atomic gate-closing transaction

Gate status changes follow this sequence:

OPEN -> IMPLEMENTED -> VERIFIED ON EXACT SHA -> INDEPENDENTLY RE-PERFORMED (when required) -> CLOSED.

No step may be skipped. Implementation and verification are separate states. A status cannot be changed to CLOSED by the same commit that merely adds code or tests without successful execution evidence.

## 5. Automatic reopening triggers

A previously closed gate MUST be reopened immediately when any of these occurs:
- a defect, bypass, false-positive, false-negative, schema drift, or contradictory evidence is found;
- the claimed result cannot be reproduced from the cited SHA and instructions;
- required evidence is missing, stale, unbound to the SHA, or shown to be from a different environment;
- a downstream gate discovers an upstream invariant was not actually enforced;
- a test suite omits a required production path or passes only through a non-production adapter;
- the production entrypoint, migrations, or runtime factory disagree about authoritative state.

Reopening does not require approval. Record the defect, affected gates, blast radius, evidence that exposed it, and the last known-good SHA. Do not delete the old record; mark it SUPERSEDED/REOPENED and preserve its audit trail.

## 6. Regression-proofing the discovered failure

For every reopened gate:
1. Add a regression test reproducing the original failure before or with the fix.
2. Add negative tests proving the unsafe/invalid path fails closed.
3. Add a positive test proving the intended path succeeds.
4. Run the regression against the actual production dependency where relevant (PostgreSQL for production persistence).
5. Re-run the full dependent gate set, not only the newly added test.
6. Bind results to the final exact SHA.
7. Independently re-perform any gate that was previously misreported as closed.

## 7. Current disposition

The prior production-readiness conclusion is not accepted as final. Production entrypoint/factory and migration/schema assertions have changed, and a previous green-gate claim was found unreliable. Therefore:
- Canonical Ledger production gate: REOPENED / NOT VERIFIED.
- Production PostgreSQL migration gate: OPEN / NOT VERIFIED.
- Deep value-truth reconciliation gate: IN PROGRESS / NOT VERIFIED.
- Overall EAI production lock: BLOCKED / NOT LOCKED.

No production-ready or green claim is permitted until fresh exact-SHA evidence satisfies this policy. This document defines a control, not evidence that the control has already passed.
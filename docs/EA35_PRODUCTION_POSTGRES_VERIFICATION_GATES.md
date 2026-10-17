# EA-35.13 — Production PostgreSQL Verification Gates

Status: IN PROGRESS / NOT LOCKED  
Branch: `feat/ea21-transaction-aware-ledger`  
Purpose: define the evidence required to close the three remaining production-readiness gates. This document is a test contract, not evidence that the gates have passed.

## Gate 1 — Migration preservation and reconciliation

### Required invariants
- Capture a read-only pre-migration snapshot of escrow aggregates, canonical/legacy account balances, movement rows, and transaction IDs.
- Run the exact versioned migration against a disposable PostgreSQL database matching the supported pre-migration schema.
- Compare pre/post account identity and currency sets; compare balances and movement history, not balances alone.
- Verify each committed value movement maps to one escrow aggregate, one witness, one matching outbox event, and completed idempotency evidence.
- Require zero unexplained differences. Any tolerated transformation must have an explicit, reviewed mapping and a quantified reconciliation record.
- Never move value during schema migration or authority cutover.

### Evidence artifact
Record migration identifier/checksum, pre/post row counts, account-set diffs, balance diffs, movement transaction-ID diffs, orphan counts, reconciliation output, PostgreSQL version, test run URL, and exact tested commit SHA.

### Fail conditions
Missing historical movement rows, currency/account mismatches, non-zero unexplained balance differences, duplicate movement IDs, missing witness/outbox/idempotency evidence, or a migration that cannot be rerun safely.

## Gate 2 — PostgreSQL crash/recovery and outbox lease

Run against real PostgreSQL, not SQLite-only tests.

### Required scenarios
1. Inject failure before transaction commit. Assert no balance, escrow, movement, witness, outbox, or idempotency partial commit.
2. Commit a value movement, then terminate the process before response delivery. Replay the same idempotency key and fingerprint. Assert no second movement.
3. Reuse the same key with a different fingerprint. Assert conflict and no value movement.
4. Create an abandoned `PROCESSING` record and run the documented recovery procedure. Assert deterministic completion or safe hold; never infer success from absence of a response.
5. Expire an outbox lease, reclaim the event, and deliver it twice. Assert the consumer's durable event deduplication prevents duplicate side effects.
6. Restart the runtime and re-run deep value-truth reconciliation.

### Required assertions
- Source and destination balances change exactly once.
- Exactly one canonical movement exists per transaction ID.
- Escrow state and version agree with the committed operation.
- Exactly one matching witness and outbox event exist for each value movement.
- Idempotency state is completed only after the corresponding transaction commits.
- A failed verification leaves the operation held; recovery must not create an alternate authority.

### Evidence artifact
PostgreSQL server version; fault-injection scenario IDs; before/after account balances and versions; movement/witness/outbox/idempotency row snapshots; recovery logs; reconciliation report; exact commit SHA; CI run URL.

## Gate 3 — Independent re-performance

The re-performer must not rely on the original test helper's expected result or merely rerun the same assertions.

### Independent procedure
1. Start from a clean disposable PostgreSQL database and apply the documented migration from scratch.
2. Seed a known escrow and two or more ledger accounts with a recorded initial-value total.
3. Execute FUND, LOCK, RELEASE, REFUND, CANCEL, and SETTLEMENT scenarios, including negative and replay cases.
4. Query persisted rows directly using an independent SQL script, not the runtime's read API.
5. Independently recompute movement integrity hashes and reconcile movement ↔ escrow ↔ witness ↔ outbox ↔ idempotency.
6. Recompute total value before/after and verify every delta from the movement history.
7. Restart the service, repeat safe replays, and confirm no additional value movement.
8. Publish results with tester identity/role, date, commands, outputs, database version, commit SHA, and any deviations.

### Independence rule
The re-performance must use a separate test run and independently authored queries/assertions. A passing unit test, SQLite test, code review, or application log alone does not satisfy this gate.

## Current verified facts and limitations

- The canonical runtime factory/entrypoint constructor mismatch was corrected in commit `e860f502f3e1a2d56fd873ad2faab7b1ab630740`.
- The repository has a PostgreSQL schema file at `postgres/schema/001_concurrency.sql`, including canonical ledger, escrow, witness, outbox, and idempotency tables.
- Presence of schema SQL is not proof it has been applied to a live PostgreSQL instance.
- SQLAlchemy `metadata.create_all` is not a substitute for applying and validating the versioned SQL migration against an existing deployment.
- No live PostgreSQL re-performance result, exact-SHA CI run, or independent evidence package is recorded by this document.

## Release decision

All three gates remain **OPEN** until evidence artifacts above are attached and reviewed. Do not label production readiness GREEN or lock EAI based on this contract alone.

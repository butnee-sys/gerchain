# EA-35 PostgreSQL Production Re-performance Evidence

Status: IN PROGRESS / NOT LOCKED

## Scope

This evidence gate validates the production PostgreSQL runtime for the canonical value-flow boundary. It does not authorize any product/application layer.

## Required evidence

1. ProductionRuntimeFactory constructs a PostgreSQL runtime.
2. Canonical Ledger is authoritative.
3. Canonical Escrow is durable.
4. Witness, Outbox, and Durable Idempotency are in the same transaction graph.
5. FUND -> LOCK -> RELEASE executes against PostgreSQL.
6. Replay does not duplicate value movement.
7. Deep value-truth reconciliation reports no unexplained issue.
8. Production entrypoint boots against PostgreSQL.
9. PostgreSQL migration/concurrency gate passes.
10. Evidence is tied to the exact tested commit SHA.

## Current correction

Production entrypoint was corrected to instantiate ProductionRuntimeFactory through ProductionRuntimeConfig and factory.create(), rather than calling create() as a class method.

Canonical production construction was also corrected to configure Canonical Ledger authority rather than the legacy PostgreSQL Release authority.

Correction commit:
e860f502f3e1a2d56fd873ad2faab7b1ab630740

## Previous PostgreSQL evidence

A PostgreSQL production gate passed on commit:
223f0d70eaa3805c3678a609d6067273b77545bc

That evidence is retained as prior evidence only. It does not establish GREEN for later commits.

## Release rule

No production lock is declared until a fresh PostgreSQL gate passes against the exact current branch tip and the result is independently re-performed.

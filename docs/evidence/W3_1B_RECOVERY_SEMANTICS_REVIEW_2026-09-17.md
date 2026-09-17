# CORE W3.1-B Recovery Semantics Review — 2026-09-17

## Finding

The current migration executor accepted a physically pre-applied target schema and then created the authoritative W3 upgrade record without provenance proving that the DDL had been executed by the CORE migration executor.

That behavior is inconsistent with the frozen W3.1-B recovery architecture: an ambiguous external failure must first reconcile against the recorded predecessor, and only a known predecessor state may be retried. A matching target schema is not sufficient evidence of authoritative execution.

## Required semantics

`DDL without committed authority` is a falsification condition, not an implicit authorization path.

The executor must:

1. lock the canonical W3 schema row;
2. verify the exact recorded predecessor physical fingerprint before executing DDL;
3. reject a target schema that already exists without a committed migration identity;
4. execute the immutable DDL only inside the authoritative transaction;
5. verify the resulting W3.1-A v1.1 physical fingerprint;
6. commit the W3 successor authority in the same transaction.

Recovery after an ambiguous failure must reconcile the actual state against the predecessor. If the predecessor matches, the migration may be retried. If the target or another unexpected state is observed, the result is a hard recovery conflict and must not be silently adopted.

## Status

W3.1-B scientific closure remains HOLD until the executor, recovery tests, F11/F12, and independent PostgreSQL reproduction are reconciled with this rule.

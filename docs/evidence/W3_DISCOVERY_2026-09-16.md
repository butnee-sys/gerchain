# CORE W3 — Discovery Evidence

## Date

2026-09-16

## Scope

CORE only. SHUUD excluded.

## Discovery result

The initial discovery found no dedicated schema-version authority or migration subsystem under the expected names. The inspected `database.py` and test fixtures used `Base.metadata.create_all`, which was correctly classified as insufficient evidence for concurrent schema/version authority.

## Superseding implementation evidence

The discovery finding is superseded for the declared W3 capability by the implementation and closure evidence on execution commit `46f9443a6a4e14e91807f75a7dd9fae619ad7131`.

The W3 implementation now defines:

- canonical schema identity and current version;
- atomic predecessor-to-successor transition semantics;
- migration identity and idempotency;
- PostgreSQL row-lock serialization and transaction boundary;
- stale predecessor rejection;
- reader committed-state boundary;
- rollback preservation;
- independent oracle and deterministic reproduction;
- independent PostgreSQL re-performance.

## Final status

**W3 = GREEN (bounded technical/scientific validation domain)**

See `docs/evidence/W3_CLOSURE_2026-09-16.md` for the reconciled closure record.

## Remaining boundary

The complete production DDL migration executor and its integration with this authority layer remain a separately declared concern. This does not invalidate the bounded W3 closure, but it limits the claim to schema/version authority and concurrency transition semantics.

W3 GREEN does not imply final CORE GREEN or CORE LOCK.

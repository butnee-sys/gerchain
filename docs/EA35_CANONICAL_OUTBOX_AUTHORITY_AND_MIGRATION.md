# EA-35 — Canonical Outbox Authority and Migration Contract

Status: **DEFINED / NOT PRODUCTION-LOCKED**  
Scope: establish one authoritative outbox for canonical GerChain value-flow transactions.

## 1. Authority decision

The only authoritative production outbox is:

- Table: `gerchain_outbox_events`
- ORM model: `persistence.recovery_outbox.OutboxEvent`
- Transaction-participating write boundary: `persistence.transactional_outbox.enqueue_in_transaction`
- Canonical schema source: `postgres/migrations/001_canonical_production.sql` and the ordered, checksummed migration chain in `postgres/migrations/__init__.py`
- Migration application and schema verification: `services/gerchain_runtime_factory.initialize_canonical_postgres_schema` and `assert_canonical_production_schema`

Value movement and its outbox intent must be committed in the same PostgreSQL transaction. The transaction-aware enqueue function must not open another session or commit. Delivery workers may claim/lease and complete committed events after the business transaction commits.

## 2. Non-authoritative legacy representation

The legacy table named `outbox` in `postgres/schema/001_concurrency.sql` is **not** the canonical production outbox. That file is a historical/compatibility schema path and must not be applied as an alternative production migration chain.

Do not drop, rename, copy, or merge a legacy `outbox` table automatically while it may contain data. First inventory it, compare event IDs/types/aggregate IDs/payloads against `gerchain_outbox_events`, identify duplicates and orphans, and preserve a rollback snapshot. Any future retirement must be an explicit, separately reviewed migration after reconciliation proves safe.

## 3. Required schema invariants

- `gerchain_outbox_events.event_id` is unique and non-null.
- `event_type`, `aggregate_id`, `payload_json`, `state`, `attempts`, `created_at`, and `updated_at` are durable.
- Event identity is deterministic for canonical value operations: `<event_type-lowercase>:<transaction_id>`.
- Reusing an event ID with different type, aggregate, or payload is a conflict, not a silent success.
- A value movement's outbox event must match both `aggregate_id = movement.escrow_id` and `event_type = GERCHAIN_<movement.operation>`.
- State-only events such as CREATE and LOCK may have witness/outbox/idempotency evidence without a ledger movement; reconciliation must not misclassify them as value movements.
- Outbox delivery is at-least-once. Consumers must be idempotent; an expired lease may cause redelivery but must never cause a second ledger movement.

## 4. Migration route

1. Apply only the ordered checksummed migration chain under `postgres/migrations/`.
2. On an empty PostgreSQL database, apply every canonical migration in order and verify the final schema.
3. On a representative legacy PostgreSQL snapshot, capture pre-migration row counts and checksums; apply the same chain; verify existing event data is preserved and required canonical metadata is present. Missing required escrow currency/refund destination must fail closed, not be fabricated.
4. Inventory any legacy `outbox` table created by the historical schema path. Keep it non-authoritative and read-only during reconciliation.
5. Run deep value-truth reconciliation and assert no missing, duplicate, mismatched, or orphaned committed value-operation evidence.
6. Record the exact commit SHA, migration versions/checksums, PostgreSQL version, test command, CI run URL, and result.

## 5. Evidence still required

This contract documents the intended authority; it is not proof that both migration scenarios have passed. The following remain open until executed against real PostgreSQL and attached to an exact commit:

- empty-database migration test;
- legacy-data migration test, including legacy outbox inventory;
- CI run for both paths;
- production entrypoint boot and complete value-operation lifecycle;
- deep reconciliation after lifecycle and restart/recovery;
- independent re-performance.

No production lock may be declared on documentation-only evidence.

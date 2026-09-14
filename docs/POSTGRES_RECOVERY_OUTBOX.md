# PostgreSQL Recovery and Outbox

GerChain uses a durable outbox as the post-commit event boundary. It is not a second workflow engine.

## Lifecycle

```text
PENDING
  ↓ claim
PROCESSING + lease
  ├── heartbeat → PROCESSING + renewed lease
  ├── complete → COMPLETED
  └── worker crash
          ↓ lease expiry
       PENDING
          ↓ retry
       PROCESSING
```

## Recovery invariant

An abandoned `PROCESSING` event becomes eligible again only after its lease expires. `FOR UPDATE SKIP LOCKED` prevents multiple workers from claiming the same row concurrently.

`event_id` is unique, so enqueue is idempotent.

## Important boundary

Outbox recovery does not infer whether an external side effect completed. The authoritative value mutation must already be protected by the same database transaction and unique transaction identity. The outbox is responsible for durable delivery/retry of the committed event.

This separation prevents the outbox from becoming a second Ledger or settlement authority.

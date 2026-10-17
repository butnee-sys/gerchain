# EA-35 Production Verification Log

## Scope

EA-35 verifies the production EAI value-flow boundary:
Canonical Ledger + durable Escrow + Witness + Outbox + Idempotency + Deep Value Truth Reconciliation.

## Verified by repository inspection

- ProductionRuntimeFactory requires a PostgreSQL URL and PostgreSQL engine.
- ProductionRuntimeFactory applies the canonical `postgres/migrations` history before constructing the runtime.
- ProductionRuntimeFactory configures Canonical Ledger authority, not the legacy Release authority.
- production_entrypoint.py constructs ProductionRuntimeConfig and the factory instance correctly.
- Production entrypoint fails closed unless Canonical Ledger authority is established.
- Canonical migration history currently contains versions 001 through 010, with deterministic version selection and checksum validation.
- EA-35 PostgreSQL workflow exists and provisions PostgreSQL 16.
- The integration test exercises production runtime boot, account creation, FUND, LOCK, RELEASE, balance assertions, evidence counts, and deep value-truth reconciliation.

## Evidence boundary

Repository inspection is implementation evidence, not execution evidence.

The current environment cannot directly execute the GitHub PostgreSQL workflow because outbound GitHub network access is unavailable from the execution container. Therefore no local PostgreSQL GREEN claim is made here.

## Release gate

EA-35 remains:

**IN PROGRESS / NOT LOCKED**

Required next evidence:

1. GitHub Actions PostgreSQL workflow execution on the exact branch tip.
2. Exact-SHA successful migration and production-runtime integration evidence.
3. Independent re-performance evidence.
4. Recovery/restart evidence.
5. Final reconciliation evidence.

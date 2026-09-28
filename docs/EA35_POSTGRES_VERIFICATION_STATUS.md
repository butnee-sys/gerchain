# EA-35 PostgreSQL Verification Status

Date: 2026-09-28

## Scope

This record covers the production PostgreSQL authority gate for EA-35. It does not lock EAI or the wider architecture.

## Source-level evidence

- Branch: `feat/ea21-transaction-aware-ledger`
- Verified branch tip at inspection: `f93c5291d409fd5fb53712cca50c01d59aa4fd08`
- Production factory constructs `ProductionRuntimeFactory` from `ProductionRuntimeConfig`.
- Factory applies the PostgreSQL migration chain from `postgres/schema` and invokes `assert_canonical_production_schema`.
- Factory configures `GerchainRuntime` with `configure_canonical_ledger` and requires canonical-ledger authority.
- Production entrypoint now constructs the factory instance correctly and calls `factory.create()`.
- Canonical schema guard requires Ledger, Escrow, Witness, Outbox and durable Idempotency tables plus the full escrow lifecycle and movement integrity constraints.

## Execution evidence

- GitHub Actions run `36362648554` — `production-postgresql-proof` — queued for PR #90 at inspection time.
- GitHub Actions run `36362645804` — `.github/workflows/canonical-postgres.yml` — completed with failure immediately and exposed no job record; therefore its failure cause is not yet established from job logs.
- Current commit combined status exposes `security/snyk (butnee-sys)` as successful.
- Multiple PostgreSQL production/re-performance workflows are queued for the same commit.

## Gate decision

**NOT LOCKED.**

No PostgreSQL execution result is promoted to GREEN until a workflow job completes and its logs demonstrate:
1. migration success,
2. canonical schema guard success,
3. production entrypoint boot,
4. canonical value-flow re-performance,
5. reconciliation tests,
6. no legacy value-authority fallback.

Queued is not PASS. Source inspection is not runtime proof.

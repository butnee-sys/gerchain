# EA-35 Production PostgreSQL Evidence

## Scope
This evidence gate covers the production runtime construction and PostgreSQL re-performance for the canonical value-flow path.

## Verified in source
- `ProductionRuntimeFactory` requires PostgreSQL.
- Factory construction creates canonical persistence metadata for Ledger, Escrow, Outbox, Idempotency, and Witness.
- Factory configures `GerchainRuntime` through `configure_canonical_ledger()`.
- Factory requires canonical ledger authority before returning.
- `production_entrypoint.py` constructs `ProductionRuntimeConfig` and invokes the factory instance correctly.
- The EA-35 PostgreSQL workflow includes:
  1. factory construction against PostgreSQL 16;
  2. production entrypoint boot;
  3. FUND → LOCK → RELEASE re-performance;
  4. REFUND and CANCEL re-performance;
  5. deep reconciliation tests;
  6. canonical runtime tests.

## Exact source correction
Production runtime construction correction commit:
`e860f502f3e1a2d56fd873ad2faab7b1ab630740`

## Verification state
Repository source verification: **IMPLEMENTED**.

GitHub Actions execution for the exact correction commit has not produced a retrievable workflow-run/status record through the available repository interface at this checkpoint. Therefore PostgreSQL execution evidence is **UNVERIFIED**, not GREEN.

## Release gate
EA-35 remains **IN PROGRESS / NOT LOCKED** until an exact-SHA PostgreSQL workflow execution demonstrates the complete gate successfully.

## Non-claims
This document does not constitute an external audit, certification, or production deployment attestation.

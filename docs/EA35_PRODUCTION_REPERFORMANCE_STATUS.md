# EA-35 Production Re-performance Status

Status: IN PROGRESS / NOT LOCKED

## Verified repository facts

- Production entrypoint requires a PostgreSQL `GERCHAIN_DATABASE_URL`.
- Production runtime construction uses `ProductionRuntimeFactory.create(...)`.
- The factory applies versioned PostgreSQL migrations from `postgres/migrations`.
- The factory configures `GerchainRuntime` with `configure_canonical_ledger()`.
- Production boot fails closed if canonical persistence tables/columns are missing.
- Production boot validates the canonical escrow state constraint.
- Canonical value authority remains `gerchain_ledger_accounts` and `gerchain_ledger_movements`.
- Legacy ReleaseAccount/AtomicRelease is not used as the production authority by the current factory.

## Current migration evidence

Migration `002_canonical_production.sql` creates the canonical ledger, witness, idempotency and transactional outbox stores and extends the legacy escrow table with production fields and lifecycle states.

Migration application is serialized by a PostgreSQL advisory transaction lock and protected by `schema_version` checksums.

## Runtime verification boundary

Repository inspection confirms the construction path is internally consistent:

GERCHAIN_DATABASE_URL
-> SQLAlchemy PostgreSQL engine
-> versioned migrations
-> canonical schema validation
-> GerchainRuntime
-> Canonical Ledger authority

However, no fresh executed PostgreSQL workflow result is currently available for the exact branch tip. Therefore this evidence is not an execution-level GREEN claim.

## Release gate

The following remain required before production lock:

1. Fresh PostgreSQL execution against the exact branch tip.
2. CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT/READ execution evidence.
3. Deep value-truth reconciliation after the transaction matrix.
4. Restart/recovery evidence with no duplicate value movement.
5. Exact-SHA CI evidence.
6. Independent re-performance.

No production lock is declared until all release gates have evidence.

## Latest GitHub Actions observation — 2026-09-28

- Branch tip observed: `65837b311dc1b68d1e368fbd3f3c023b9885642f`.
- `canonical-production-postgres` run: `36376807081` — **QUEUED**, conclusion `null`.
- Its `postgres-canonical` job: **QUEUED**.
- Multiple PostgreSQL/EAI production workflows for the same branch tip are also queued; no completed execution result was available at verification time.

This is positive evidence that the gate was triggered, but it is **not execution evidence of success**.

## Exact failure evidence — 2026-10-01

The GitHub Actions run associated with commit `e860f502f3e1a2d56fd873ad2faab7b1ab630740` completed with release-blocking failures:

- `core-gates`: Python collection failed because that exact commit contained literal escaped newline sequences in `services/gerchain_runtime.py`.
- `PostgreSQL Concurrency`: migration serialization failed with a `schema_version` primary-key conflict on version 2.

The current branch source has since corrected the runtime formatting and the migration runner now uses conflict-safe version recording. A fresh exact-current-SHA execution is still required; these historical failures are not classified as current GREEN evidence.

# EA-35 PostgreSQL Production Evidence

Status: **VERIFIED TECHNICAL EVIDENCE / NOT PRODUCTION LOCK**

## Exact verified commit
- Branch: `feat/ea21-transaction-aware-ledger`
- Commit: `a3bc73d9258300b07201a141006415185125e64a`
- Execution date: 2026-09-27
- PostgreSQL service: 16

## Primary verified GitHub Actions runs

All primary runs below are associated with the exact commit above.

1. **PostgreSQL production runtime**
   - Run: `36288686456`
   - Conclusion: **success**
   - PostgreSQL 16 service initialized
   - Dependencies installed
   - Real PostgreSQL production boot completed successfully

2. **canonical-production-postgres**
   - Run: `36288686504`
   - Conclusion: **success**
   - Production factory construction succeeded
   - Canonical production schema verification succeeded
   - `is_canonical_ledger_authoritative == True`
   - Deep value-truth test suite completed successfully

3. **EA-35 PostgreSQL production re-performance**
   - Run: `36288686428`
   - Conclusion: **success**
   - Canonical PostgreSQL migrations applied successfully
   - Real PostgreSQL production integration suite completed successfully
   - FUND → LOCK → RELEASE lifecycle verified
   - Canonical balances verified
   - Durable escrow state verified
   - Deep value-truth reconciliation verified
   - Restart/replay RELEASE idempotency verified without duplicate value movement

Additional same-commit production evidence also completed successfully:
- PostgreSQL production smoke: `36288686386`
- EAI Production PostgreSQL Re-performance: `36288686490`
- EAI PostgreSQL Reperformance: `36288686465`
- production-postgres-proof: `36288686589`
- production-postgres-reperformance: `36288686508`
- Production PostgreSQL Runtime: `36288456388`
- production-postgres-smoke: `36288456442`
- PostgreSQL production proof: `36288686563`
- production-postgres-evidence: `36288686515`
- Production Runtime PostgreSQL: `36288686550`
- CodeQL Advanced: `36288686502`
- core-gates: `36288686479`

## Verified production construction

The current production factory:
1. requires a PostgreSQL URL;
2. applies versioned PostgreSQL migrations;
3. runs the canonical production schema guard;
4. constructs `GerchainRuntime`;
5. configures Canonical Ledger authority;
6. requires Canonical Ledger authority before returning the runtime.

The production entrypoint:
1. requires PostgreSQL `GERCHAIN_DATABASE_URL`;
2. requires escrow, amount, currency and witness configuration;
3. constructs the runtime through `ProductionRuntimeFactory`;
4. verifies `is_canonical_ledger_authoritative`;
5. supports controlled SIGTERM/SIGINT shutdown;
6. disposes the engine in a `finally` block.

## Verified canonical value-flow coverage

The successful EA-35 PostgreSQL evidence covers:
- FUND → Canonical Ledger
- LOCK → durable Canonical Escrow state
- RELEASE → Canonical Ledger
- durable Witness evidence
- durable Outbox evidence
- durable Idempotency evidence
- movement integrity binding
- deep value-truth reconciliation
- replay/idempotency behavior
- production runtime construction and restart boundary

## Non-successful workflows on the same commit

The repository also reported failures in some duplicate/legacy workflow paths on this exact commit:

- PostgreSQL Concurrency: run `36288456348`
  - concurrency suite step succeeded;
  - subsequent canonical production value-truth gate failed.
- CORE Operating Reconciliation: run `36288456384`
  - operating reconciliation integration suite failed.
- Production PostgreSQL Verification: run `36288456359`
  - production factory/schema verification succeeded;
  - canonical persistence test suite failed.

These are **not reclassified as GREEN**. Their failing assertions/logs must be resolved or explicitly classified before final production lock.

Other workflows were still in progress when this evidence was recorded and are therefore not used as proof.

## Interpretation

This is fresh technical evidence from real PostgreSQL 16 GitHub Actions execution. It is stronger than source inspection alone.

It does **not** by itself constitute:
- external independent audit attestation;
- IAM/MFA governance approval;
- disaster-recovery approval;
- capacity/performance approval;
- final production authorization.

Therefore:

**EA-35 PostgreSQL primary technical gates = VERIFIED**

**EAI / overall production lock = NOT YET**

Latest primary EA-35 re-performance evidence is now verified on exact branch tip `a3bc73d9258300b07201a141006415185125e64a`.

The primary EA-35 gate executed against real PostgreSQL 16 and verified factory construction, production entrypoint boot, FUND→LOCK→RELEASE, REFUND/CANCEL, deep value-truth reconciliation, and canonical runtime tests. However, several duplicate/legacy workflow paths still report failures on the same SHA. These are not reclassified as GREEN and are not treated as part of the primary EA-35 evidence until their scope is explicitly retired or corrected.

Next gate: independent re-performance and final production-control evidence. Overall production lock remains NOT YET.

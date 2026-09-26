# EA-35 PostgreSQL Production Evidence

Status: **VERIFIED TECHNICAL EVIDENCE / NOT PRODUCTION LOCK**

## Exact verified commit
- Branch: `feat/ea21-transaction-aware-ledger`
- Commit: `c31eb97a40479f623fb0bb63566edd27912ab58a`
- Execution date: 2026-09-26
- PostgreSQL: 16.15
- Python: 3.13.15

## Verified GitHub Actions runs

All runs below are associated with the exact commit above.

1. **production-postgres-evidence**
   - Run: `36210526982`
   - Conclusion: **success**
   - Production factory boot: success
   - Deep reconciliation: **19 passed**

2. **Production PostgreSQL Runtime**
   - Run: `36210526942`
   - Conclusion: **success**
   - Production entrypoint boot against PostgreSQL: success
   - Production PostgreSQL value-flow proof: success
   - Test result: **4 passed**

3. **production-postgres-reperformance**
   - Run: `36210526915`
   - Conclusion: **success**
   - PostgreSQL canonical production re-performance: **1 passed**

4. **Production PostgreSQL verification**
   - Run: `36210527059`
   - Conclusion: **success**
   - Production bootstrap: success
   - Full value-flow proof: success
   - Deep value reconciliation: success

5. **EAI Production PostgreSQL Re-performance**
   - Run: `36210526977`
   - Conclusion: **success**
   - Production factory construction: success
   - Real PostgreSQL canonical lifecycle proof: success
   - Deep value-truth reconciliation: success
   - Observed results: **1 passed + 1 passed + 19 passed**

6. **PostgreSQL production re-performance**
   - Run: `36210527088`
   - Conclusion: **success**

## Verified production path

The current production factory:
1. requires PostgreSQL;
2. applies versioned migrations;
3. executes the canonical production schema guard;
4. constructs `GerchainRuntime`;
5. configures Canonical Ledger authority;
6. requires Canonical Ledger authority before returning the runtime.

The production entrypoint:
1. requires a PostgreSQL `GERCHAIN_DATABASE_URL`;
2. requires escrow, amount, currency and witness configuration;
3. constructs the runtime through `ProductionRuntimeFactory.from_engine()`;
4. verifies `is_canonical_ledger_authoritative`;
5. supports controlled SIGTERM/SIGINT shutdown;
6. disposes the engine in a `finally` block.

## Verified canonical value-flow coverage

The PostgreSQL evidence covers:
- FUND → Canonical Ledger
- LOCK → durable Canonical Escrow state
- RELEASE → Canonical Ledger
- REFUND → authoritative refund destination
- CANCEL → authoritative original sender reversal
- durable Witness evidence
- durable Outbox evidence
- durable Idempotency evidence
- movement integrity binding
- deep value-truth reconciliation
- replay/idempotency behavior
- production runtime balance and escrow reads

## Interpretation

This is fresh technical evidence from PostgreSQL 16 GitHub Actions execution. It is stronger than source inspection alone.

It does **not** by itself constitute:
- external independent audit attestation;
- IAM/MFA governance approval;
- disaster-recovery approval;
- capacity/performance approval;
- final production authorization.

Therefore:

**EA-35 PostgreSQL technical gate = VERIFIED**

**EAI production lock = NOT YET**

Next gate: independent re-performance and remaining production-control evidence.

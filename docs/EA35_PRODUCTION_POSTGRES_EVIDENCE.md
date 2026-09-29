# EA-35 Production PostgreSQL Evidence

Date: 2026-09-26

## Exact execution commit
08d260af1f921f038c93786007bd92d2199c6145

Open verification PR: #90 — EA-35.13 PostgreSQL production smoke gate.

## Direct PostgreSQL production evidence

GitHub Actions run 36231750283 — Production PostgreSQL verification:
- PostgreSQL 16 service
- production dependencies installed
- production PostgreSQL bootstrap: 1 passed
- production full value flow: 2 passed
- deep value reconciliation: 19 passed
- complete job conclusion: success

GitHub Actions run 36231750320 — Production PostgreSQL Runtime:
- production entrypoint boot against PostgreSQL: success
- production PostgreSQL value-flow proof: success
- runtime contract suite: 4 passed
- complete job conclusion: success

## Re-performance evidence

GitHub Actions run 36231750336 — production-postgres-reperformance:
- real PostgreSQL service
- tests/postgres/test_production_postgres_reperformance.py -m postgres
- 1 passed
- complete job conclusion: success

The re-performance test independently exercises the PostgreSQL persistence boundary and verifies:
- Canonical Ledger authority
- FUND
- LOCK
- RELEASE
- escrow terminal state
- canonical balances
- movement count
- Witness evidence
- Outbox evidence

GitHub Actions run 36231750279 — EAI PostgreSQL Reperformance: success.
GitHub Actions run 36231750333 — PostgreSQL production re-performance: success.
GitHub Actions run 36231750255 — production-postgresql-proof: success.

## EAI matrix evidence

GitHub Actions run 36231750286 — PostgreSQL production proof: success.
The EAI matrix covers FUND → LOCK → REFUND, FUND → CANCEL, SETTLEMENT, canonical balances, terminal escrow states, and deep value reconciliation.

## Architecture conclusion

The verified PostgreSQL production path exercises:
Canonical Ledger → Canonical Escrow → Witness → Outbox → Durable Idempotency → Deep Value Truth Reconciliation

No legacy in-memory balance authority is required for the verified PostgreSQL production path.

## Status

EA-35 PostgreSQL production verification: VERIFIED at exact commit 08d260af1f921f038c93786007bd92d2199c6145.

This is repository/CI technical evidence, not external certification or independent organizational audit.

EA-35 overall: IN PROGRESS / NOT LOCKED.

Remaining closure gates:
1. reconcile all overlapping/open EA-35 PRs into one canonical execution baseline;
2. formally record independent re-performance evidence with exact SHA and methodology;
3. verify production entrypoint/recovery semantics after final branch consolidation;
4. update final evidence index;
5. only then consider production lock.

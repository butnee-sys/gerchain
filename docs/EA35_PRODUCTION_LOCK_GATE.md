# EA-35 — Production Lock Gate

Status: IN PROGRESS / NOT LOCKED

## Purpose

This document is the release gate for production readiness of the fundamental GerChain value-flow architecture and EAI boundary.

A component may be marked LOCKED only when the required evidence is fresh, reproducible, and tied to an exact commit.

## Verified evidence at current branch

Branch: `feat/ea21-transaction-aware-ledger`

Latest production-entrypoint correction:
`e860f502f3e1a2d56fd873ad2faab7b1ab630740`

Security status for that exact commit:
- `security/snyk (butnee-sys)`: SUCCESS

Code-level authority checks:
- Canonical Ledger authority is explicit in `GerchainRuntime`.
- Production factory configures `configure_canonical_ledger()`.
- Production entrypoint constructs `ProductionRuntimeConfig` and `ProductionRuntimeFactory` correctly.
- Legacy Release authority is not the production construction path.
- Production runtime requires Canonical Ledger authority.

## Not yet verified

The following remain release blockers:

1. Fresh PostgreSQL production boot against a real PostgreSQL instance.
2. Existing-schema migration compatibility; SQLAlchemy `create_all()` is not a migration mechanism.
3. Full canonical schema completeness for Ledger, Escrow, Witness, Outbox and Idempotency.
4. End-to-end PostgreSQL execution for CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT/READ.
5. Deep Value Truth Reconciliation on PostgreSQL.
6. Crash/restart and abandoned-processing recovery on PostgreSQL.
7. Exact-SHA CI evidence for the production test suite.
8. Independent re-performance.
9. Physical freeze/removal of legacy value authorities after migration evidence.

## Lock rule

No GREEN or LOCKED declaration may be made from code inspection alone.

Required sequence:

```
CODE
→ SCHEMA
→ REAL POSTGRESQL
→ END-TO-END TRANSACTION TEST
→ DEEP VALUE-TRUTH RECONCILIATION
→ RECOVERY
→ CI
→ INDEPENDENT RE-PERFORMANCE
→ FINAL EVIDENCE
→ PRODUCTION LOCK
```

## Current decision

**EA-35: IN PROGRESS / NOT LOCKED**

The current evidence supports implementation progress, not final production certification.

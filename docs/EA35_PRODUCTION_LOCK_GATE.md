# EA-35 — Production Lock Gate

Status: VERIFIED / NOT LOCKED

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

## Verified on exact SHA

The following release gates are evidenced on `98f8f9005d58220dece4a1e44b36e8bc452b8069`:

- Production PostgreSQL runtime — run `37420203547` — SUCCESS.
- Independent PostgreSQL evidence — run `37420203563` — SUCCESS.
- Production PostgreSQL gate — run `37420203612` — SUCCESS.

The production gate completed syntax, canonical factory/schema, PostgreSQL boot, deep value-truth reconciliation, EAI re-performance, and real PostgreSQL value-flow checks. Independent evidence separately verified persisted PostgreSQL value state.

## Remaining release blockers

1. Physical freeze/removal/archive closure of legacy value authorities.
2. Organizational IAM/MFA evidence.
3. Privileged-access review evidence.
4. Branch/main governance evidence.
5. Final independent assurance package.
6. Overall fundamental architecture reconciliation and final evidence consolidation.

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

**EA-35: VERIFIED / NOT LOCKED**

The current evidence supports production PostgreSQL verification. Final lock remains withheld pending the remaining closure gates.

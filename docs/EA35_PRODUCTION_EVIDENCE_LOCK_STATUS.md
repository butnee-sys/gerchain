# EA-35 — Production PostgreSQL Evidence and Lock Status

**Branch:** `feat/ea21-transaction-aware-ledger`  
**Evidence baseline:** `98f8f9005d58220dece4a1e44b36e8bc452b8069`  
**Evidence date:** 2026-10-06

## Status

**EA-35: VERIFIED / NOT LOCKED**

The production PostgreSQL execution gates passed on the exact implementation line after the migration-concurrency correction.

## Exact workflow evidence

| Evidence | Workflow run | Result |
|---|---:|---|
| Production PostgreSQL runtime | 37420203547 | SUCCESS |
| Independent PostgreSQL evidence | 37420203563 | SUCCESS |
| Production PostgreSQL gate | 37420203612 | SUCCESS |

### Production PostgreSQL runtime

Run `37420203547` completed successfully.

Verified:
- canonical PostgreSQL migration and boot;
- production PostgreSQL value flow;
- deep value-truth suite.

### Independent PostgreSQL evidence

Run `37420203563` completed successfully.

Verified:
- independently persisted-value verification against PostgreSQL.

### Production PostgreSQL gate

Run `37420203612` completed successfully.

Verified:
- exact evidence commit recording;
- Python syntax gate;
- production factory and canonical persistence;
- production entrypoint boot against PostgreSQL;
- deep reconciliation;
- EAI production re-performance;
- real PostgreSQL production value-flow gate.

The production entrypoint emitted:

`GerChain production runtime initialized: escrow=ci-escrow-1 currency=USD`

The same gate reported:
- deep reconciliation: **19 passed**;
- EAI PostgreSQL re-performance: **1 passed**;
- production PostgreSQL gate: **1 passed**.

## Correction validated by this evidence

The previous migration-concurrency defect produced:

`duplicate key value violates unique constraint "schema_version_pkey"`

Migration execution was changed to use a transaction-scoped PostgreSQL advisory lock and one migration transaction. The production gate subsequently passed.

## EAI conclusion

The evidence demonstrates that:

**Escrow-as-Infrastructure → PostgreSQL durable state → Canonical Ledger → Witness → Outbox → Idempotency → Deep Value Truth Reconciliation**

can execute as one production-tested infrastructure path.

This does not create a new architecture layer. EAI remains the infrastructure principle implemented through the frozen G3/CORE architecture.

## Lock boundary

EA-35 is **verified but not globally locked**.

Global production lock remains dependent on broader assurance gates, including:
- legacy persistence removal/archive closure;
- organizational IAM/MFA evidence;
- privileged-access review;
- branch/main governance evidence;
- final independent assurance package;
- overall fundamental architecture reconciliation.

**No product-layer work is authorized by this document.**

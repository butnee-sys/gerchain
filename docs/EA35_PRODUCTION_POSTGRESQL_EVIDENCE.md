# EA-35 Production PostgreSQL Evidence

Status: **VERIFIED — NOT A PRODUCTION LOCK**

## Verified branch / commit
- Branch: `feat/ea21-transaction-aware-ledger`
- Exact verified commit: `c4cd095d440145b7689758234c19fbee75e02b72`
- Evidence date: 2026-10-06

## Fresh GitHub Actions evidence

| Evidence | Run | Result |
|---|---:|---|
| production-postgresql-gate | 37416549634 | **SUCCESS** |
| independent-postgresql-evidence | 37416549659 | **SUCCESS** |

Both runs executed against the exact commit above and used a real PostgreSQL 16 service.

## production-postgresql-gate

Run `37416549634` completed successfully.

Verified stages:
1. Python syntax gate.
2. Production factory and canonical persistence.
3. Production entrypoint boot against PostgreSQL.
4. Deep value-truth reconciliation tests.
5. EAI production re-performance.
6. Real PostgreSQL production value-flow gate.

The gate explicitly verifies:
- PostgreSQL-only production runtime;
- canonical persistence tables;
- Canonical Ledger authority;
- Ledger movement idempotent replay;
- production entrypoint initialization;
- deep reconciliation;
- EAI lifecycle re-performance;
- real PostgreSQL value-flow.

## EAI production re-performance

The EAI re-performance covers, in one real PostgreSQL transaction environment:
- FUND → LOCK → RELEASE;
- FUND → LOCK → REFUND;
- FUND → CANCEL;
- CREATED → CANCEL;
- SETTLEMENT;
- final balances;
- final escrow states;
- deep value-truth reconciliation.

The test asserts that the canonical Ledger remains the sole monetary value authority and that witness/outbox/idempotency evidence reconciles with committed value movements.

## independent-postgresql-evidence

Run `37416549659` completed successfully.

This verification reads persisted PostgreSQL facts directly and independently checks:
- account balances;
- movement operation/source/destination/amount/currency;
- movement integrity hashes;
- escrow state/version;
- witness records;
- outbox records;
- durable idempotency records.

## Production entrypoint

The exact verified commit contains the corrected production construction path:

`GERCHAIN_DATABASE_URL`
→ `ProductionRuntimeConfig`
→ `ProductionRuntimeFactory`
→ canonical PostgreSQL persistence
→ `configure_canonical_ledger()`
→ `require_canonical_ledger_authority()`

The entrypoint boot test completed successfully against PostgreSQL.

## Conclusion

**EA-35.13 PostgreSQL production gate: VERIFIED.**

This is strong repository-level technical evidence from a real PostgreSQL 16 execution environment. It is not external certification or third-party production sign-off.

**EA-35 overall remains IN PROGRESS / NOT LOCKED** until the remaining final evidence, operational governance, privileged-access/IAM, recovery/DR, and release-lock gates are formally closed.


## EA-35.13 verified evidence — 2026-10-06

- Initial production smoke head: `48b2fcbd802e0607f92f0e1ed90c940d0ca71e2b`
- Initial production PostgreSQL run: `37438638354` — SUCCESS
- Initial EAI PostgreSQL Production Proof: `37438638438` — SUCCESS
- Initial independent PostgreSQL evidence: `37438638329` — SUCCESS
- Full-lifecycle extension initially exposed a test expectation error only: actual persisted evidence was 9 witnesses/outbox/idempotency records, while the test expected 8.
- Corrected tested head: `3d8b3c5da54f7f6c4a9721190b851380d9cc010d`
- Corrected production PostgreSQL run: `37438978065` — SUCCESS
- Corrected independent PostgreSQL evidence: `37438978112` — SUCCESS
- Corrected production PostgreSQL gate: `37438978166` — SUCCESS
- Corrected gate verified: syntax; production factory and canonical persistence; production entrypoint boot against PostgreSQL; deep value-truth tests; EAI production re-performance; real PostgreSQL value-flow including FUND, LOCK, RELEASE, REFUND, CANCEL and SETTLEMENT.
- PostgreSQL service: version 16.
- Full lifecycle reconciliation: matched; canonical movement count 7; witness count 9; outbox count 9.

### Gate decision
EA-35.13 production PostgreSQL re-performance is **VERIFIED** for the corrected tested commit above. This is repository technical evidence, not an external certification or final production lock.

### Remaining lock gates
- recovery/restart evidence
- security/IAM/MFA governance evidence
- final independent re-performance and release evidence reconciliation
- formal production lock decision

# EA-35.13 PostgreSQL Re-performance Evidence

Status: VERIFIED / NOT LOCKED

## Exact source
- Branch: `feat/ea21-transaction-aware-ledger`
- Head SHA: `45579c0112fb3a3a3a76d3895832eb67ce280e99`

## Authoritative verification run
- Workflow: PostgreSQL production re-performance
- Run ID: `36213114696`
- Run number: `1368`
- Conclusion: SUCCESS
- Head SHA: `45579c0112fb3a3a3a76d3895832eb67ce280e99`

## Verified gates
The successful workflow executed:
1. PostgreSQL 16 service startup and health check.
2. ProductionRuntimeFactory construction.
3. Canonical Ledger authority assertion.
4. Production entrypoint boot against PostgreSQL with controlled timeout.
5. PostgreSQL canonical value-flow re-performance.
6. PostgreSQL refund/cancel re-performance.
7. EA-35 deep value-truth reconciliation tests.
8. Canonical runtime value-flow tests including refund, cancel, settlement and canonical-ledger runtime behavior.

## Independent EAI PostgreSQL evidence
- Workflow: EAI Production PostgreSQL Re-performance
- Run ID: `36213114630`
- Run number: `1841`
- Conclusion: SUCCESS
- Head SHA: `45579c0112fb3a3a3a76d3895832eb67ce280e99`
- Verified steps included production factory construction, real PostgreSQL canonical lifecycle proof, and deep value-truth reconciliation.

## Important qualification
This evidence verifies the EA-35 PostgreSQL gate at the exact SHA above. It does NOT by itself establish the final production lock. Other repository-wide workflows on the same branch include unrelated or broader failures; those remain separate release gates and must not be represented as EA-35 GREEN.

## Next locked work
1. Preserve this evidence.
2. Resolve/triage repository-wide failures that affect the fundamental production gate.
3. Repeat the exact-SHA verification after any corrective change.
4. Independent re-performance and final production-lock evidence remain open.


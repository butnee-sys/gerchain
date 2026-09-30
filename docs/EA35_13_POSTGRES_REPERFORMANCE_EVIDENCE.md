# EA-35.13 PostgreSQL Re-performance Evidence

Status: VERIFIED / NOT LOCKED

## Exact execution commit
- Branch: `feat/ea21-transaction-aware-ledger`
- Exact execution SHA: `890a78f36dcfe161e195da649b3cd124133d6535`
- Production factory/entrypoint correction commit `e860f502f3e1a2d56fd873ad2faab7b1ab630740` is an ancestor of the execution SHA.

## Authoritative verification runs
- Workflow: PostgreSQL production re-performance
- Run ID: `36317914217`
- Run number: `699`
- Conclusion: SUCCESS
- Job: `postgres-reperformance`
- Verified steps: production runtime construction, PostgreSQL production re-performance, deep value-truth tests.

- Workflow: Production PostgreSQL Runtime
- Run ID: `36317914351`
- Run number: `1113`
- Conclusion: SUCCESS
- Job: `production-postgres-runtime`
- Verified steps: production runtime and migrations.

- Workflow: production-postgres-smoke
- Run ID: `36317914313`
- Run number: `810`
- Conclusion: SUCCESS
- Verified steps: real PostgreSQL smoke test and production entrypoint boot.

- Workflow: production-postgres-proof
- Run ID: `36317914446`
- Run number: `1053`
- Conclusion: SUCCESS
- Verified step: PostgreSQL canonical proof.

- Workflow: production-postgresql-gate
- Run ID: `36317914344`
- Run number: `87`
- Conclusion: SUCCESS
- Verified step: PostgreSQL production value-truth gate.

- Workflow: PostgreSQL production verification
- Run ID: `36317914254`
- Run number: `1968`
- Conclusion: SUCCESS
- Verified steps: production factory construction and persistence/reconciliation tests.

## Verified EA-35 execution properties
1. PostgreSQL 16 service starts and becomes healthy.
2. ProductionRuntimeFactory constructs successfully.
3. Canonical Ledger authority is established.
4. Production entrypoint boots against real PostgreSQL.
5. Canonical value-flow execution succeeds.
6. REFUND and CANCEL re-performance succeeds.
7. SETTLEMENT uses the Canonical Ledger path.
8. Replay/idempotency behavior succeeds.
9. Deep value-truth reconciliation succeeds.
10. Canonical runtime value-flow tests succeed.

## EAI re-performance
- Workflow: EAI PostgreSQL Reperformance
- Run ID: `36317914266`
- Run number: `863`
- Conclusion: SUCCESS
- Job: `eai-postgres-reperformance`
- Verified on the same exact execution commit through a real PostgreSQL service.
- This is an independent execution workflow; it is not an independent implementation/oracle.

## Qualification
This evidence proves the PostgreSQL production execution gate for EA-35.13 on the exact execution SHA above. It does not by itself establish the final production lock.

Repository-wide unrelated/broader workflows may still be open or failing. Those are separate release gates and must be resolved or explicitly accepted before the overall fundamental architecture can be locked.

## Next gate
- Preserve exact-SHA evidence.
- Reconcile repository-wide production gates.
- Perform final independent re-performance/oracle review.
- Repeat verification after any corrective change.
- Final production lock remains OPEN.


## Current verification refresh — 2026-09-30
- Current branch tip: `d0bf3dd0f0736ac9778d3d6c5e32ffed9a6f5902`
- `Production PostgreSQL verification`: Run `36671893611` — SUCCESS.
  - Real PostgreSQL production lifecycle: SUCCESS
  - Production PostgreSQL value flow: SUCCESS
  - Deep value reconciliation: SUCCESS
- `Production PostgreSQL Smoke`: Run `36671893517` — SUCCESS.
  - Production runtime boot and canonical schema: SUCCESS
- The current branch therefore has fresh exact-SHA evidence for PostgreSQL boot, canonical schema initialization, value-flow execution, and deep reconciliation.
- Other workflows triggered by this same commit were still QUEUED at the time of this evidence refresh; they are not treated as verified here.
- Final production lock remains OPEN until the queued/repository-wide gates and independent re-performance are resolved.

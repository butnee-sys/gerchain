# EA-35 FINAL LOCK

Status: SUPERSEDED — NOT VALID FOR CURRENT TIP

Superseded historical lock SHA: d182d33681403bf14fad80cb357ddb3bd1f395bc
Current verification target SHA: 4e336c4b8e0f766e188887a90a52791987ae6a56

## Reason

The historical lock was issued for an earlier exact SHA. The current branch contains subsequent production-runtime, migration, and Runner-gate changes and therefore requires fresh exact-SHA evidence.

The current SHA MUST NOT be declared locked until the live GitHub Actions gates complete successfully for this exact SHA.

## Required fresh gates

- EA-35 Runner Gate
- production-postgres
- production-postgresql-e2e
- production-postgres-evidence
- EAI PostgreSQL Production Proof
- production PostgreSQL re-performance
- independent PostgreSQL evidence
- canonical/fundamental architecture gates
- CORE operating reconciliation
- DEE security / CodeQL as applicable

## Current status

Runner execution is currently queued. No current-SHA PASS has been established.

Therefore:

**EA-35 = IN PROGRESS / NOT LOCKED**

Historical successful evidence remains historical evidence and cannot be silently promoted to current-SHA evidence.

## Lock rule

Only after every required current-SHA gate is successful may this document be replaced by a FINAL LOCK document recording:
1. exact locked SHA;
2. exact successful run IDs;
3. PostgreSQL production proof;
4. EAI proof;
5. Deep Value Truth proof;
6. Recovery proof;
7. Independent re-performance;
8. Evidence Index;
9. final lock decision.

No downstream product-layer work is authorized by this status.

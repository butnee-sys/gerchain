# EA-35 PostgreSQL Production Evidence

Status: **VERIFIED — PRODUCTION POSTGRESQL GATE PASSED**

Evidence date: 2026-10-07  
Branch: `feat/ea21-transaction-aware-ledger`  
Verified baseline commit: `db2b057c4e8d823dde11cca971f12cf0ec447158`

Superseding branch-tip verification: `041f2babdd90a6eb521e0b2af4b9c19c39cd4454`

## Primary production gate

Workflow: `production-postgresql-gate`  
Run: `37571470436` (baseline evidence)  
Job: `112631018984` (baseline evidence)  
Conclusion: **success**

All production gate steps passed:

1. Python syntax gate
2. Production factory + canonical persistence verification
3. Production entrypoint boot against PostgreSQL 16
4. Concurrent PostgreSQL migration bootstrap
5. Deep value-truth reconciliation suite
6. EAI production re-performance
7. Real PostgreSQL production value-flow gate

Fresh test evidence from the gate includes:

- 19 deep reconciliation tests passed
- 1 EAI PostgreSQL re-performance test passed
- 2 PostgreSQL production value-flow tests passed

## Branch-tip verification

Workflow: `production-postgresql-gate`  
Run: `37572041414`  
Job: `112632620410`  
Head SHA: `041f2babdd90a6eb521e0b2af4b9c19c39cd4454`  
Conclusion: **success**

This branch-tip run re-executed the full production PostgreSQL gate after the runtime-construction corrections. The job completed successfully.

## Independent PostgreSQL evidence

Workflow: `independent-postgresql-evidence`  
Run: `37571470428`  
Job: `112630845484`  
Conclusion: **success**

Independent persisted-value verification:

- 1 test passed
- PostgreSQL 16 service container used
- production persistence was exercised against a real PostgreSQL instance

## EAI production proof

Workflow: `EAI PostgreSQL Production Proof`  
Run: `37571470409`  
Job: `112630845561`  
Conclusion: **success**

The EAI production proof completed successfully against PostgreSQL 16.

## Additional production workflow

Workflow: `production-postgres`  
Run: `37571470410`  
Job: `112630846191`  
Conclusion: **success**

Verified:

- production PostgreSQL migration and boot
- production PostgreSQL value flow
- deep value-truth suite

## Production entrypoint evidence

The production entrypoint now constructs the runtime through:

`ProductionRuntimeConfig → ProductionRuntimeFactory → configure_canonical_ledger → require_canonical_ledger_authority`

The PostgreSQL production gate explicitly booted `production_entrypoint.py` and verified controlled startup.

## Interpretation

This evidence establishes that the **EAI / Canonical PostgreSQL runtime path is executable and reproducible in CI against PostgreSQL 16** at the verified commit.

It does **not** by itself constitute final overall production lock. Remaining gates include repository-wide governance/security controls, final architecture evidence reconciliation, recovery/DR evidence, release governance, and final independent re-performance/approval where required.

**Important:** GREEN here means fresh repository/CI technical evidence only. It is not an external certification or operational production attestation.

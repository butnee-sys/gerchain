# EA-35 Production Master Gate — Evidence Review

**Review date:** 2026-10-20  
**Repository:** `butnee-sys/gerchain`  
**Exact SHA reviewed:** `02c30ea85d570e658664d9fdfe8dec9d5132fdc0`  
**Decision:** `NOT_LOCKED`  
**Scope:** Evidence review only. This record does not promote any open gate to success.

## Exact-SHA workflow evidence

- PostgreSQL re-performance: [run 39433071309](https://github.com/butnee-sys/gerchain/actions/runs/39433071309) — **SUCCESS**, exact SHA matched.
- Production master gate: [run 39433071155](https://github.com/butnee-sys/gerchain/actions/runs/39433071155) — **FAILURE by design of the fail-closed controller**, because required architecture-level evidence was missing/open.
- PostgreSQL evidence artifact: `ea35-postgres-evidence-02c30ea85d570e658664d9fdfe8dec9d5132fdc0`, SHA-256 digest reported by GitHub: `ed37f6277be89781a55426ff9af2c6c96609f57ae50cf1d54d1ed6e7589f0250`.
- Master decision artifact: `production-master-gate-02c30ea85d570e658664d9fdfe8dec9d5132fdc0`, SHA-256 digest reported by GitHub: `0472679b835a05430fc8ca587aadcef73958dded786ee40efbfff7eabb2a105a`.

## PostgreSQL gates reported successful

The exact-SHA PostgreSQL workflow reported success for compile, regression, PostgreSQL connection, migration atomicity, legacy upgrade, lifecycle, migration concurrency, publication integrity, entrypoint, production boot, migration catalog, deep reconciliation, and manifest. Its job also reported successful execution of the canonical lifecycle, rollback/replay tests, factory boot, actual entrypoint boot, and independent-process migration concurrency regression.

This is repository CI evidence for the tested commit and isolated PostgreSQL job; it is not an external independent audit or proof of production operations against a live customer deployment.

## Architecture gates still open

The master-gate decision log marked these gates `open`:

1. `error_duplicate_excess`
2. `cross_store_reconciliation`
3. `authority_boundary`
4. `core_correctness`
5. `adapter_boundaries`
6. `eai_g3_governance`
7. `transaction_correctness`
8. `recovery`
9. `auditability`
10. `security_iam_mfa`
11. `observability`
12. `performance_stress`
13. `disaster_recovery`
14. `ci_release_governance`
15. `independent_reperformance`
16. `final_evidence_bundle`

`inventory_map` was marked successful. A successful PostgreSQL run was not accepted as a substitute for architecture-level evidence, which is the correct fail-closed behavior.

## Required evidence to close remaining gates

| Gate | Minimum evidence required before marking success |
|---|---|
| Error / duplicate / excess | Complete inventory of duplicate and legacy paths, explicit disposition, tests proving no parallel authoritative value path |
| Cross-store reconciliation | Exact-SHA report matching accounts, movements, escrow transitions, witness, idempotency and outbox with no unexplained discrepancies |
| Authority boundary | Code-path inventory and negative tests proving legacy stores and application endpoints cannot mutate authoritative value |
| CORE correctness | Traceable tests for atomicity, idempotency, concurrency, rollback and invariants against the canonical transaction boundary |
| Adapter boundaries | Contract tests for every frozen layer-to-layer adapter, including fail-closed negative cases |
| EAI / G3 governance | Machine-checkable Trust, Transparency and Performance conditions tied to Decision → Authorization → Release |
| Transaction correctness | PostgreSQL tests for lifecycle, duplicate/replay, conflicting replay, failure rollback, concurrent operations and value conservation |
| Recovery | Crash/abandoned-processing, outbox lease, retry, restart and no-double-movement evidence |
| Auditability | Reconstructable operation-to-movement-to-witness-to-outbox-to-idempotency evidence, with tamper/mismatch negatives |
| IAM / MFA | Actual privileged identity inventory, MFA enforcement evidence, access review and least-privilege verification |
| Observability | Health/readiness, structured operational events, metrics/alerts and evidence that critical failures are observable |
| Performance / stress | Reproducible workload, declared thresholds, concurrency profile and measured results against the target environment |
| Disaster recovery | Backup/restore and recovery exercise, RPO/RTO measurement, integrity reconciliation after restore |
| CI / release governance | Protected branch/review policy evidence, required checks, release provenance and exact-SHA binding |
| Independent re-performance | A reviewer/process independent of implementation reruns the documented steps and signs the result |
| Final evidence bundle | Complete manifest, exact SHA, artifact checksums, all gate records and final decision report |

## Release rule

Do not mark an open gate successful based on documentation alone. Each gate must link to a specific reproducible artifact, test result, policy export, or independent report bound to the release candidate SHA. The master gate must then be rerun on that exact SHA.

**Status remains: IN PROGRESS / NOT LOCKED.**

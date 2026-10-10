# EA-35.13 PostgreSQL Production Evidence

Status: IN PROGRESS / NOT LOCKED

Fresh-gate trigger: 2026-10-08 historical PostgreSQL concurrency run failed on duplicate schema_version version 2; historical CORE-gates run failed during collection with a SyntaxError in services/gerchain_runtime.py. These results are not evidence against the current branch head: current branch source has since been updated, including the conflict-safe migration publisher and a valid production runtime factory/entrypoint. A fresh exact-head workflow run is required to establish whether those corrections pass.

This evidence marker exists to force a fresh PostgreSQL production-gate execution against the current branch tip.

Required gates:
1. Canonical ProductionRuntimeFactory construction.
2. Canonical persistence table bootstrap.
3. Canonical Ledger movement and replay/idempotency.
4. Production entrypoint boot against PostgreSQL 16.
5. Migration bootstrap verification.
6. Deep value-truth reconciliation.
7. EAI production re-performance.
8. Full PostgreSQL production value-flow integration.

Current verified code contracts: production_entrypoint.build_production_runtime() validates PostgreSQL URL and required environment, constructs ProductionRuntimeConfig, calls ProductionRuntimeFactory.create(), and asserts Canonical Ledger authority; initialize_canonical_postgres_schema() applies postgres/migrations through apply_migrations() before ORM metadata creation. Source inspection is not execution proof. A successful canonical-postgres-gate run at the exact resulting commit, with all required PostgreSQL lifecycle, migration concurrency/checksum, boot, and reconciliation steps passing, is required before this evidence can be classified GREEN.

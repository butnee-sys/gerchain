# EA-34.13 — Production Entrypoint Cutover

Status: IN PROGRESS / NOT LOCKED

Docker previously executed node_cli.py, which instantiated NEFStateEngine + TransactionManager in memory. That was a production entrypoint mismatch.

The Docker entrypoint now executes production_entrypoint.py.

Production entrypoint requirements:
- GERCHAIN_DATABASE_URL must be PostgreSQL.
- GERCHAIN_ESCROW_ID is required.
- GERCHAIN_ESCROW_AMOUNT is required and integer.
- GERCHAIN_CURRENCY is required.
- GERCHAIN_WITNESS_ID is required.

Boot sequence:
Docker
→ production_entrypoint.py
→ SQLAlchemy PostgreSQL engine
→ ProductionRuntimeFactory
→ Canonical Ledger / Escrow / Witness / Idempotency / Outbox metadata
→ GerchainRuntime.configure_canonical_ledger()
→ fail closed unless canonical ledger authority is established.

The legacy node_cli.py remains in the repository as a legacy/test CLI and is no longer the Docker production entrypoint.

Important limitation:
This cutover changes the container boot authority, but production deployment evidence is not yet verified. CI, real PostgreSQL boot, schema migration, readiness/health semantics, and independent re-performance remain OPEN.

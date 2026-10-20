# CORE / NEF / G-3 Production Change Audit
Date: 2026-10-12
Repository: `butnee-sys/gerchain`
Base: `621e7e2acefe243d4c72e783970e1eb833c60b96`
Reviewed head: `77a78e8c92b6564aa4ac9290b4db4810b5cdd0e5`
Status: **IN PROGRESS / NOT LOCKED**

## 1. Evidence boundary
The GitHub comparison reports 84 commits ahead, 0 behind. `services/gerchain_runtime.py` changed by +345/-59 lines. This is a change-size fact, not a correctness or production-readiness result.
The exact head SHA currently has zero GitHub check runs and no PR-triggered workflow runs returned by the connector. CI = **UNVERIFIED**. No live PostgreSQL execution evidence was available during this review. PostgreSQL = **UNVERIFIED**.

## 2. Runtime change inventory

| Change group | Files / symbols | Architectural classification | Transaction / recovery / evidence assessment | Verification |
|---|---|---|---|---|
| Canonical Ledger attachment | `GerchainRuntime.configure_canonical_ledger`, `is_canonical_ledger_authoritative`, `require_canonical_ledger_authority` | Authority | Separates production Ledger boundary from test-memory MoneyLedger; flag is runtime configuration evidence, not proof of schema/DB readiness | Code inspected; CI and PostgreSQL unverified |
| Account creation and balance reads | `create_account`, `get_balance`, `CanonicalLedgerRead` | Value authority | Intended to make canonical ledger accounts the only production balance truth | Unit/integration tests exist in repository; exact-SHA CI unverified |
| Escrow state read | `get_escrow_state`, `get_escrow` | Durable truth | Reads durable aggregate rather than memory state | Code inspected; PostgreSQL unverified |
| FUND | `fund_escrow_in_transaction` | Value authority + atomic transition | Source-to-escrow movement and CREATED→FUNDED in caller transaction; must prove DB constraints and rollback against PostgreSQL | Tests exist; CI/PG unverified |
| LOCK | `lock_escrow_in_transaction` | State-only transition | FUNDED→LOCKED with witness/outbox/idempotency, no value movement; reconciliation must not require a movement for LOCK | Negative/positive SQLite-backed tests exist; PostgreSQL unverified |
| RELEASE | `release_escrow_in_transaction` | Value authority + authorization | LOCKED→RELEASED with canonical Ledger, durable idempotency and evidence; beneficiary authority still needs review because runtime supplies destination | Tests exist; CI/PG unverified |
| REFUND | `refund_escrow_in_transaction` | Value authority + destination protection | Destination is read from authoritative escrow refund_destination, not caller argument | Test exists; CI/PG unverified |
| CANCEL | `cancel_escrow_in_transaction` | State/value transition | CREATED cancellation state-only; FUNDED cancellation reverses value to original sender | Tests exist; CI/PG unverified |
| SETTLEMENT | `SettlementCoordinator` | Orchestration | Delegates to Canonical Ledger; must remain non-authoritative and own no separate balance/movement store | Tests exist; CI/PG unverified |
| Atomic cross-record operation | `AtomicValueTransaction` | Atomicity / evidence | Couples Ledger movement, escrow transition, witness, outbox and durable idempotency in caller transaction; rollback and replay tests are necessary but do not substitute for PostgreSQL | Tests exist; CI/PG unverified |
| Deep reconciliation | `deep_value_reconciliation.py` | Integrity / auditability | Checks movement ↔ escrow ↔ witness ↔ outbox ↔ idempotency plus integrity hash; LOCK is intentionally state-only | Negative matrix exists; CI/PG unverified |
| Legacy API/UI mutations | `api/v1.py`, `gerchain/web_ui.py` | Boundary protection | Legacy direct mutation endpoints fail closed with HTTP 410; must confirm all production routes and alternate runtimes are covered | Code-level claim only; runtime verification open |
| Entrypoint/factory | `production_entrypoint.py`, `services/gerchain_runtime_factory.py` | Deployment authority | Factory is now instance-created and configures Canonical Ledger; metadata create_all is not a versioned migration system and must not be mistaken for migration completion | Static inspection only; boot unverified |

## 3. Blocking schema mismatch found

At this reviewed head, `persistence/atomic_ledger.py` declares `gerchain_ledger_movements.operation`, `escrow_id`, and `integrity_hash`. However, `postgres/schema/004_ea26_value_flow_persistence.sql` creates `gerchain_ledger_movements` with only transaction_id, source, destination, amount, currency, and created_at; it does **not** add those three columns.

The deep reconciliation code reads those fields, and canonical value-flow code writes them. On a database initialized from the SQL migration, this mismatch can break inserts or reconciliation. `Base.metadata.create_all()` does not retrofit missing columns on an existing table. Therefore production boot/runtime readiness cannot be certified until a forward migration adds the missing columns (with safe backfill/nullability strategy) and a real PostgreSQL test applies migrations from an empty database and from a prior-schema database.

Additional migration gate: `production_entrypoint.py` calls factory initialization that uses SQLAlchemy metadata `create_all`; it does not demonstrate ordered application of versioned SQL migrations. Treat schema initialization and schema migration as separate responsibilities.

## 4. NEF / G-3 / CORE boundary review

| Component | Frozen responsibility | Review result | Remaining proof |
|---|---|---|---|
| NEF | Authoritative asset registration, valuation and verification truth | Canonical architecture file and `architecture/nef_gerchain.py` inspected; adapter requires asset/valuation/verification identifiers and VALID status | Integration test proving stale/invalid asset version fails closed in PostgreSQL-backed value movement |
| G-3 | Condition/escrow/governance policy; Trinity = Trust + Transparency + Performance | `architecture/g3_core.py` and `architecture/composition_root.py` inspected; G-3 gates flow, Core retains operational value authority | Negative matrix for each missing/failed Trinity element, Decision and Authorization, attached to exact CI run |
| CORE / GerChain | Canonical operational value-flow truth | Canonical Ledger + durable escrow paths implemented in code | Live PostgreSQL migration, concurrency, rollback, replay, recovery and deep reconciliation evidence |
| DEE | Ecosystem protection/governance, not duplicate engines | Frozen architecture unchanged in reviewed range | Verify every runtime route uses explicit adapter and no bypass remains |
| Adapter boundaries | Explicit, fail-closed layer-to-layer interfaces | Frozen map unchanged; selected adapters inspected | Automated route/bypass inventory and tests |

## 5. Change evidence register

Evidence states:
- **CODE-INSPECTED** = source reviewed.
- **TEST-PRESENT** = relevant test file exists; does not mean it passed at this SHA.
- **CI-UNVERIFIED** = no exact-SHA successful check evidence.
- **POSTGRESQL-UNVERIFIED** = no real PostgreSQL execution evidence.
- **OPEN** = further implementation or independent evidence required.

| ID | Claim | Evidence | State |
|---|---|---|---|
| C-001 | Runtime can attach Canonical Ledger | `services/gerchain_runtime.py` | CODE-INSPECTED |
| C-002 | FUND/LOCK/RELEASE/REFUND/CANCEL use durable operations in canonical mode | runtime + `persistence/*_escrow.py` | CODE-INSPECTED; CI-UNVERIFIED |
| C-003 | Settlement delegates to canonical Ledger | `persistence/settlement_coordinator.py` | CODE-INSPECTED; CI-UNVERIFIED |
| C-004 | Movement has operation/escrow/integrity fields | ORM model | CODE-INSPECTED |
| C-005 | SQL migration supplies same movement fields | schema 004 | **FAIL / MISMATCH** |
| C-006 | Deep reconciliation validates cross-store evidence | `persistence/deep_value_reconciliation.py` | CODE-INSPECTED; CI-UNVERIFIED |
| C-007 | Production factory initializes versioned schema migrations | factory/entrypoint | **NOT ESTABLISHED** |
| C-008 | Exact reviewed SHA CI is green | GitHub check-runs returned zero | **UNVERIFIED** |
| C-009 | Real PostgreSQL lifecycle and recovery pass | no execution evidence supplied | **UNVERIFIED** |
| C-010 | Independent re-performance completed | no independent report | **OPEN** |

## 6. Required next sequence

1. Add a forward PostgreSQL migration for missing ledger movement columns; define safe backfill and constraints.
2. Add migration versioning/runner; do not rely on `create_all` as migration.
3. Add PostgreSQL integration tests for clean install and upgrade from the previous schema.
4. Exercise lifecycle: CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL, SETTLEMENT, READ; include rollback, same-request replay, conflicting replay, concurrency and restart recovery.
5. Run deep reconciliation after each scenario and after restart.
6. Trigger CI for the exact resulting commit and preserve run/job evidence.
7. Expand the NEF/G-3/CORE register with exact test names, workflow run IDs, DB version, migration revision and result.
8. Independent re-performance before any production lock.

**Decision: NO PRODUCTION LOCK.** The schema/model mismatch is a concrete blocker, not merely missing paperwork.

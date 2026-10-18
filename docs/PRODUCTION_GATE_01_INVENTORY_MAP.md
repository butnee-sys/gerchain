# Production Gate 1 — Inventory and Dependency Map

**Status:** CLOSED / FINAL LOCKED (Gate 1 only)  
**Repository:** `butnee-sys/gerchain`  
**Branch:** `feat/ea21-transaction-aware-ledger`  
**Scope:** Fundamental architecture + EAI production-readiness workstream. Product/application layers are excluded.

## 1. Closure criterion

Gate 1 is closed when the authoritative architecture, runtime entrypoints, value/state/evidence stores, adapters, migration path, legacy/alternate paths, and unresolved assurance boundaries are enumerated in one traceable map. This is a source/repository inventory closure; it does not claim the entire system is production-ready or independently certified.

## 2. Canonical architecture inventory

| Layer / boundary | Canonical responsibility | Authoritative boundary / evidence | Inventory status |
|---|---|---|---|
| DE | Top-level Digital Economy space | Frozen architecture document | Mapped |
| DE Adapter | Controlled entry into DEE | `architecture/boundary_adapters.py`, `architecture/composition_root.py` | Mapped |
| DEE | Ecosystem governance, protection, trust, coordination; not a duplicate engine | `architecture/composition_root.py`, `architecture/governed_flow_adapters.py` | Mapped |
| DEE ↔ G3 Adapter | Explicit, fail-closed boundary | `architecture/governed_flow_adapters.py` | Mapped |
| G3 Escrow Foundation | Conditions, escrow policy, governance policy; Trinity = Trust + Transparency + Performance | `architecture/g3_core.py`, `services/g3_core_handler.py` | Mapped |
| G3 ↔ CORE Adapter | Explicit hand-off; no direct bypass | `architecture/composition_root.py`, `architecture/boundary_adapters.py` | Mapped |
| NEF + GerChain | NEF owns asset registration/valuation/verification truth; GerChain owns operational value-flow truth | `architecture/nef_gerchain.py`, `nef_gerchain_port/nef_adapter.py`, `nef_gerchain_port/gerchain_adapter.py` | Mapped |
| CORE engines | Ledger, Money, Escrow, Witness, Verification, Decision, Authorization, Release, Settlement, Reconciliation, Audit, Consensus, Recovery; boundaries remain distinct | `services/gerchain_runtime.py`, `persistence/` | Mapped |
| EXIM boundary | External-system boundary; cannot bypass core adapters | Frozen architecture document; composition root | Mapped |
| I2B | External business gateway | Frozen architecture document | Mapped |
| MultiConnector | Routes State / Company / Person without owning parallel authoritative truth | Frozen architecture document | Mapped |
| PDEIZ | Protection concept over NEF + G3 + GerChain, not a new canonical layer | Architecture invariants in the project record | Mapped |

Canonical invariants retained:
- Each layer-to-layer connection uses an explicit adapter.
- Decision → Authorization → Release is mandatory.
- No second authoritative Ledger, Witness Chain, or Escrow Engine.
- No application-owned production value truth.
- Unknown/unresolved required conditions fail closed.
- One-time value movement requires database atomicity and durable idempotency.
- Recovery cannot duplicate value movement.
- NEF owns asset truth; GerChain owns operational value-flow truth; G3 governs conditions and does not become a third operational core.

## 3. Production runtime and entrypoints

| Path | Current role | Authority classification | Required control |
|---|---|---|---|
| `production_entrypoint.py` | Intended Docker production entrypoint; validates PostgreSQL URL and required env; builds factory; checks canonical authority and DB connectivity | Canonical production candidate | Must be proven on exact SHA by PostgreSQL boot/restart gate |
| `services/gerchain_runtime_factory.py` | Applies versioned migrations, checks canonical schema and migration history, creates runtime with canonical Ledger | Canonical production constructor | Migration/constraint checks must pass; no silent fallback |
| `services/gerchain_runtime.py` | Runtime API; canonical PostgreSQL mode attaches Ledger boundary | Canonical when explicitly configured; default memory mode is test-only | Production must fail closed if canonical authority absent |
| `node_cli.py` | Legacy/in-memory CLI | Non-production | Must not be the Docker production entrypoint |
| `network/api_server.py` | Legacy/in-memory API path | Non-production/alternate | Must not become production value authority |
| `api/v1.py` legacy escrow mutation | Previous direct SQLite mutation path | Disabled/fail-closed path (HTTP 410 per runtime audit) | Keep disabled; no direct state/value mutation |
| `gerchain/web_ui.py` legacy balance mutation | Previous application-owned balance mutation | Disabled/fail-closed path (HTTP 410 per runtime audit) | Keep disabled; no direct balance mutation |

## 4. Canonical state, value, and evidence stores

| Concern | Canonical source/boundary | Non-authoritative or supporting stores | Invariant |
|---|---|---|---|
| Account balance | `gerchain_ledger_accounts` | `MoneyLedger`, `ReleaseAccount`, `AccountBalance`, SQLite balances | No production balance mutation outside Canonical Ledger |
| Value movement | `gerchain_ledger_movements` via `PostgreSQLAtomicLedger.transfer_in_transaction` | Legacy release/settlement movement tables | One movement truth; durable idempotency |
| Escrow aggregate/state | `CanonicalEscrow` via `persistence/escrow_aggregate.py` | Legacy `ReleaseEscrow`, SQLite escrow state | One durable escrow state machine |
| Witness evidence | Transaction-aware Witness path / `TransactionWitness` | Legacy `ReleaseWitness`, in-memory `WitnessChain` | One authoritative witness path |
| Outbox | `OutboxEvent` / canonical transactional outbox | Legacy or duplicate outbox representation | Committed value operation has matching event; delivery is recoverable |
| Idempotency | Durable idempotency records in the value transaction | In-memory `IdempotencyEngine` | Same key + same fingerprint replays; different fingerprint conflicts |
| Audit | Audit evidence path | Not interchangeable with witness | Audit and witness remain separate responsibilities |
| Reconciliation | `persistence/value_reconciliation.py`, `persistence/deep_value_reconciliation.py` | Manual/balance-only comparison | Balance equality alone is not value-truth equality |

## 5. Operation-to-boundary map

| Operation | Canonical path | Required evidence / invariant |
|---|---|---|
| CREATE | Durable Escrow aggregate boundary | CREATED state; no value movement; durable operation evidence |
| FUND | `persistence/fund_escrow.py` → Canonical Ledger + Escrow transition | Source → escrow; CREATED → FUNDED atomically |
| LOCK | `persistence/lock_escrow.py` → durable Escrow transition | FUNDED → LOCKED; state-only, zero Ledger movements |
| RELEASE | `persistence/release_escrow.py` → Canonical Ledger | LOCKED → RELEASED; Decision + Authorization + Trinity + verified evidence |
| REFUND | `persistence/refund_escrow.py` → Canonical Ledger | LOCKED → REFUNDED; destination comes from authoritative refund destination |
| CANCEL | `persistence/cancel_escrow.py` → Canonical Ledger when FUNDED | CREATED state-only cancel; FUNDED cancel reverses to authoritative sender |
| SETTLEMENT | `persistence/settlement_coordinator.py` → Canonical Ledger | Coordinator owns no separate balance/movement truth |
| READ balance | `persistence/canonical_ledger_read.py` | Reads Canonical Ledger only |
| READ escrow | `persistence/escrow_aggregate.py` durable read | Reads canonical aggregate only |
| Recovery | Durable recovery/outbox/idempotency path | No duplicate value movement; failed verification remains held |

## 6. Migration and production schema map

- Versioned migration registry: `postgres/migrations/__init__.py`.
- Production schema bootstrap/guard: `initialize_canonical_postgres_schema` in `services/gerchain_runtime_factory.py`.
- Factory checks PostgreSQL dialect, applies migration registry, creates canonical ORM-owned metadata, verifies required constraints and schema version history (versions 1–17).
- This source inventory confirms that the migration/guard path exists; it does not itself prove a fresh database or supported existing database passed on the current tip.
- A successful production gate must bind migration output, schema checks, runtime boot, operation flow, reconciliation, recovery, and CI to one exact commit SHA.

## 7. Legacy / alternate authority freeze inventory

Explicitly non-authoritative for production value mutation:
- `money.ledger.MoneyLedger`
- `persistence.atomic_release.ReleaseAccount`
- `persistence.atomic_settlement.AccountBalance`
- `persistence.atomic_release.ReleaseEscrow`
- `persistence.atomic_release.ReleaseWitness`
- `persistence.atomic_settlement.SettlementMovement`
- SQLite `database/db.py` account balances and escrow state/value
- `gerchain/database.py` SQLite fallback
- `node_cli.py` and `network/api_server.py` memory paths

Physical removal/archive and proof that no unlisted production writer remains are not inferred from this inventory.

## 8. Known assurance gaps carried forward

These are explicitly outside Gate 1 closure and remain open unless later exact-SHA evidence closes them:
1. Full production migration + runtime boot/recovery evidence on one exact current SHA.
2. Legacy value-store physical freeze/removal/archive with data reconciliation.
3. IAM/MFA and privileged-access organizational evidence.
4. Main-branch governance / branch protection evidence.
5. Independent re-performance of the full architecture and value-truth proof package.
6. Overall fundamental architecture / EAI production lock.

## 9. Gate 1 conclusion

The architecture, runtime entrypoints, operation boundaries, authoritative stores, legacy/alternate paths, migration registry, and remaining assurance gaps are now explicitly inventoried and cross-mapped in this document.

**Gate 1 — INVENTORY / MAP: CLOSED for repository/source inventory scope.**  
**Overall production readiness: NOT LOCKED.**  
**No production GREEN status is inferred solely from this inventory.**

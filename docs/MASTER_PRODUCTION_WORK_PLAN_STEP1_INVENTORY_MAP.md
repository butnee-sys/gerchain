# MASTER PRODUCTION WORK PLAN — STEP 1
## Fundamental Architecture Inventory and Authority Map

**Disposition:** CLOSED — INVENTORY / MAPPING DELIVERABLE COMPLETE  
**Release status:** NOT LOCKED; Step 1 closure is not a production certification  
**Branch reviewed:** `feat/ea21-transaction-aware-ledger`  
**Recorded:** 2026-10-19  
**Scope:** Fundamental architecture + EAI (Escrow as Infrastructure). Product/application feature layers remain outside this gate.

## 1. Closure boundary

Step 1 closes the inventory and mapping task: the frozen canonical architecture, authoritative owners, runtime entrypoints, durable value/evidence stores, adapters, legacy alternatives, and production verification gaps are explicitly mapped below. It does **not** claim that every component has passed runtime testing, that PostgreSQL migration/recovery has been proven, or that the system is production-ready. Those are separate release gates and must remain OPEN until exact-commit evidence exists.

## 2. Frozen architecture reference

Canonical freeze: `docs/DEE_ARCHITECTURE_FREEZE.md` (freeze date 2026-09-14; recorded frozen blob `0940d8aae8858d34604eb9d7174a8afc636bb2f`).

Canonical path:

`DE → DE Adapter → DEE → DEE↔G-3 Adapter → G-3 Escrow Foundation → G-3↔CORE Adapter → NEF + GerChain Core Infrastructure → CORE↔EXIM Adapter → EXIM Port → EXIM↔I2B Adapter → I2B → I2B↔Multi-Connector Adapter → Multi-Connector (State/Company/Person) → Digital Economy Activities`

Architecture invariants inventoried:
- DE is the top-level Digital Economy space; EXIM is the external-system boundary; they are not interchangeable.
- Every layer-to-layer connection uses an explicit adapter.
- G-3 owns escrow/condition/governance policy; it is not a third operational core.
- NEF is authoritative for asset registration, valuation, and verification truth.
- GerChain's Canonical Ledger is intended to be the sole production operational value-flow authority.
- One authoritative Escrow state machine, Witness path, Outbox path, and durable idempotency boundary are allowed.
- Release is Decision → Authorization → Release; no direct release path.
- No application-owned balance truth, silent fallback, or downstream mutation of protected truth.
- Trust + Transparency + Performance are mandatory release conditions.
- Unknown/unresolved required conditions fail closed (deny/hold).
- Atomic release/value movement, durable idempotency, transactional evidence/outbox, and recovery without duplicate value movement are mandatory.
- Existing production schema upgrades require versioned migrations; ORM metadata creation alone is not migration evidence.

## 3. Authority and component inventory

| Concern | Intended authoritative owner / path | Located implementation | Inventory disposition |
|---|---|---|---|
| Canonical architecture | Frozen architecture document | `docs/DEE_ARCHITECTURE_FREEZE.md` | FROZEN reference |
| Production startup/configuration | PostgreSQL-only factory and entrypoint | `production_entrypoint.py`; `services/gerchain_runtime_factory.py` | MAPPED; boot evidence still required |
| Schema migration | Versioned PostgreSQL migration registry | `postgres/migrations/`; `postgres/migrations/apply_migrations` | MAPPED; clean/repeat/upgrade execution evidence required |
| Current balance truth | Canonical Ledger accounts | `gerchain_ledger_accounts`; `persistence/atomic_ledger.py` | DESIGNATED sole production authority |
| Value movement truth | Canonical Ledger movements | `gerchain_ledger_movements`; `PostgreSQLAtomicLedger.transfer_in_transaction` | DESIGNATED sole production mutation boundary |
| Balance reads | Canonical Ledger read model | `persistence/canonical_ledger_read.py` | MAPPED |
| Escrow aggregate/state | Durable canonical Escrow | `persistence/escrow_aggregate.py` and lifecycle modules under `persistence/` | MAPPED; lifecycle must be proven on PostgreSQL |
| Atomic operation orchestration | Shared transaction boundary | `persistence/atomic_value_transaction.py` | MAPPED; rollback/replay evidence required |
| Durable idempotency | Canonical idempotency records | `persistence/durable_idempotency.py` | MAPPED; concurrent/restart cases required |
| Witness evidence | One canonical transaction-witness path | `persistence/atomic_value_transaction.py`; Witness ORM base | MAPPED; integrity/restart proof required |
| Outbox delivery evidence | One canonical transactional outbox | `persistence/transactional_outbox.py`; `persistence/recovery_outbox.py` | MAPPED; lease/retry/restart proof required |
| Cross-store truth check | Read-only deep reconciliation | `persistence/deep_value_reconciliation.py` | MAPPED; must run against real PostgreSQL on exact candidate |
| Production runtime composition | Canonical Ledger runtime configuration | `services/gerchain_runtime_factory.py`; `services/gerchain_runtime.py` | MAPPED; factory/entrypoint contract source corrected; boot not yet certified |
| G-3 policy / release conditions | Condition/governance policy boundary | G-3 adapter/core implementation | MAPPED; end-to-end policy enforcement evidence required |
| NEF asset truth boundary | NEF ↔ GerChain adapter | `nef_gerchain_port/`; `architecture/nef_gerchain.py` | MAPPED; end-to-end integration proof required |
| External-system boundary | EXIM Port and adapter | frozen architecture / adapter modules | MAPPED |
| Business gateway | I2B and explicit adapter | frozen architecture / adapter modules | MAPPED |
| Legacy in-memory balances | Non-authoritative only | `money/ledger.py`, `MoneyLedger` | LEGACY; must never be production authority |
| Legacy PostgreSQL balance stores | Non-authoritative only | `ReleaseAccount`, `AccountBalance` and related old stores | LEGACY; freeze/archive/removal and reconciliation remain gates |
| Legacy SQLite stores / runtime | Non-authoritative only | `database/db.py`, `gerchain/database.py`, legacy CLI/server paths | LEGACY; must not be silently selected in production |
| Legacy API/UI mutation bypasses | Fail closed or controlled adapter only | legacy API/UI endpoints | MAPPED; current-tip reachability and tests must be evidenced |
| Security / IAM / privileged access | Organizational and technical controls | repository controls + external governance evidence | OPEN; code alone cannot prove organizational MFA/access review |
| CI / independent assurance | Exact-SHA workflow and independent re-performance | GitHub workflow/check evidence and retained logs | OPEN / UNVERIFIED until attached to exact candidate SHA |

## 4. Production operation inventory

| Operation | Intended durable authority | Required atomic/evidence relationship |
|---|---|---|
| CREATE | Canonical Escrow | Durable CREATED state + witness/audit/outbox/idempotency; no value movement |
| FUND | Canonical Ledger + Escrow | Source → escrow; CREATED → FUNDED; movement, state, witness, outbox, idempotency commit atomically |
| LOCK | Canonical Escrow | FUNDED → LOCKED; state-only operation; must not fabricate a Ledger movement |
| RELEASE | Canonical Ledger + Escrow | Escrow → authoritative beneficiary; LOCKED → RELEASED; Decision/Authorization/Trinity/evidence checks |
| REFUND | Canonical Ledger + Escrow | Escrow → stored authoritative refund destination; LOCKED → REFUNDED |
| CANCEL | Canonical Escrow; Canonical Ledger when funded | CREATED cancellation is state-only; FUNDED cancellation reverses value to authoritative origin |
| SETTLEMENT | SettlementCoordinator over Canonical Ledger | Orchestration only; no second balance or movement authority |
| READ BALANCE | CanonicalLedgerRead | Reads canonical Ledger only |
| READ ESCROW | Durable canonical Escrow | Reads authoritative durable aggregate only |
| RECOVERY | Canonical operation state + transactional evidence | Detect → Isolate → Hold → Diagnose → Reconcile → Recover → Verify → Audit; verification failure stays HOLD |

## 5. Cross-store evidence graph

Every value-moving operation must reconcile:

`Canonical movement ↔ transaction_id ↔ escrow_id / operation / amount / currency / source / destination`

and bind to:
- one matching transaction witness;
- one operation- and aggregate-matched outbox event;
- one completed durable idempotency record with matching request fingerprint;
- one recomputable integrity hash;
- a valid durable Escrow state consistent with the operation.

State-only operations (notably LOCK and CREATED→CANCELLED) must be distinguished from value-moving operations. Do not infer an orphan idempotency record from missing movement when the record schema does not explicitly identify the operation type.

**Invariant:** Balance equality ≠ value-truth equality.

## 6. Legacy / duplicate authority disposition

The inventory assigns one intended production authority:
- Balance and movement: Canonical Ledger.
- Escrow state: canonical durable Escrow aggregate.
- Asset truth: NEF.
- Conditions/governance: G-3.
- Witness and outbox: one authoritative path each.
- Settlement: coordinator only, not a second Ledger.

The following are classified non-authoritative for production: MoneyLedger in-memory balances, ReleaseAccount, AccountBalance, legacy ReleaseEscrow/ReleaseWitness/settlement movement representations, SQLite balance/escrow stores, legacy in-memory runtime paths, and application-owned balance mutation.

This is a logical authority designation, not evidence that legacy tables have already been physically removed or all writes have been operationally frozen.

## 7. Step 1 exit checklist

- [x] Frozen canonical architecture reference and layer path recorded.
- [x] Authority owner mapped for each foundational domain.
- [x] Production entrypoint, runtime factory, migration registry, and runtime authority path located.
- [x] Canonical balance/movement, escrow, witness, outbox, idempotency, and reconciliation components mapped.
- [x] CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT/READ/RECOVERY operations mapped.
- [x] Legacy/duplicate stores and bypass categories assigned non-authoritative / fail-closed disposition.
- [x] Atomic evidence graph and value-truth invariants recorded.
- [x] Residual runtime, schema, security, CI, and independent-assurance gaps explicitly separated from inventory closure.
- [ ] Exact-candidate PostgreSQL migration/boot/lifecycle/recovery evidence — release gate, not a source-inventory checkbox.
- [ ] Exact-SHA full CI and independent re-performance — release gate, not a source-inventory checkbox.

## 8. Final disposition

**STEP 1 — INVENTORY / MAP: CLOSED.** The architecture and authority inventory is complete as a repository mapping deliverable.

**This closure does not certify runtime behavior or production readiness.** PostgreSQL execution, migration upgrade/repeatability, lifecycle/replay/rollback/recovery, exact-SHA CI, security/governance evidence, legacy write freeze, and independent re-performance remain explicit open gates. Do not advance the production release status on the basis of source inventory alone.

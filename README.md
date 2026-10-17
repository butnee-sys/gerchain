# GerChain

**GerChain is core infrastructure for governed digital-economic value flow.**

This repository contains the production-oriented core infrastructure of the canonical digital-economy architecture. Its purpose is to provide a durable, auditable and fail-closed foundation for conditional value movement.

> **We do not move value on hope. Value moves only when structurally verified trust exists.**

---

## 1. Canonical architecture

The canonical architecture was frozen on **2026-09-14** in:

`docs/DEE_ARCHITECTURE_FREEZE.md`

The frozen path is:

```text
DE
 ↓
DE Adapter
 ↓
DEE
 ↓
DEE ↔ G-3 Adapter
 ↓
G-3 Escrow Foundation
 ↓
G-3 ↔ Core Adapter
 ↓
NEF + GerChain Core Infrastructure
 ↓
Core ↔ EXIM Adapter
 ↓
EXIM Port
 ↓
EXIM ↔ I2B Adapter
 ↓
I2B
 ↓
I2B ↔ Multi-Connector Adapter
 ↓
Multi-Connector
 ├── State
 ├── Company
 └── Person
 ↓
Digital Economy Activities
```

### Fundamental rule

> **Layer → Adapter → Layer**

No layer may bypass its defined adapter boundary to reach another layer's internal implementation.

The architecture is frozen. Implementation changes must conform to the frozen architecture unless an explicit architecture-change proposal is approved.

---

## 2. Core infrastructure responsibilities

### DE — Digital Economy

The top-level economic space. DE is mandatory and must not be bypassed.

### DEE — Digital Economy Ecosystem

The ecosystem-level environment for governance, protection, trust, policy, security, coordination, identity, access, compliance, risk control, audit policy, data governance and recovery policy.

DEE does **not** duplicate the operational value engines.

### G-3 — Escrow Foundation

G-3 establishes **Escrow as Infrastructure**.

```text
G1 = Escrow as Tool
G2 = Escrow as Service
G3 = Escrow as Infrastructure
```

G-3 governs:

- Condition Policy
- Escrow Policy
- Governance Policy
- Trust
- Transparency
- Performance

G-3 defines the conditions under which value may move. It does not become a second operational Escrow Engine.

### NEF

NEF is the authoritative infrastructure for:

- asset registration
- asset valuation
- asset verification

NEF is authoritative for **asset truth**.

### GerChain

GerChain is the operational infrastructure for **asset value flow**.

The production value authority is the Canonical Ledger.

---

## 3. Escrow as Infrastructure — EAI

**EAI = ESCROW AS INFRASTRUCTURE.**

EAI is an architectural principle, not an additional architecture layer.

Escrow is treated as infrastructure for conditional economic value movement rather than merely as a transaction tool or application service.

The structural trust chain is:

```text
Truth
  ↓
Condition
  ↓
Verification
  ↓
Decision
  ↓
Authorization
  ↓
Controlled Execution
  ↓
Evidence
  ↓
Audit
  ↓
Recovery
```

Therefore:

> **Trust = Verified alignment of Truth, Condition, Authority, Execution and Evidence.**

The corresponding infrastructure principle is:

> **Escrow = Trust-conditioned value movement infrastructure.**

---

## 4. Canonical value authority

GerChain has **one authoritative production value boundary**.

### Authoritative

```text
gerchain_ledger_accounts
        +
gerchain_ledger_movements
        +
PostgreSQLAtomicLedger.transfer_in_transaction()
        +
CanonicalLedgerRead
```

The hard invariant is:

> **No production operation may mutate a balance outside the Canonical Ledger mutation boundary.**

### Non-authoritative legacy/test stores

The following must not be used as production value authorities:

- `money.ledger.MoneyLedger`
- `gerchain_release_accounts`
- `gerchain_account_balances`
- legacy SQLite balance/value stores
- application-owned balance mutation paths
- legacy Release/Settlement value stores

Production paths must fail closed rather than silently falling back to a legacy value authority.

Reference:

`docs/EA34_LEGACY_VALUE_AUTHORITY_FREEZE.md`

---

## 5. Canonical value-flow operations

The production target is a single authoritative Ledger boundary for:

| Operation | Value authority | Evidence |
|---|---|---|
| CREATE | Canonical Escrow aggregate | state/evidence |
| FUND | Canonical Ledger | witness + outbox + idempotency |
| LOCK | Canonical Escrow state | witness + outbox + idempotency; no value movement |
| RELEASE | Canonical Ledger | witness + outbox + idempotency |
| REFUND | Canonical Ledger | witness + outbox + idempotency |
| CANCEL | Canonical Ledger when value must reverse | witness + outbox + idempotency |
| SETTLEMENT | Canonical Ledger | transaction evidence |
| READ | Canonical Ledger | authoritative balance read |

The following boundaries remain distinct:

```text
Escrow
≠ Decision
≠ Authorization
≠ Release
≠ Settlement
≠ Reconciliation
```

---

## 6. Transaction correctness

A canonical value movement is designed to bind the relevant evidence inside one database transaction:

```text
BEGIN
  ↓
Idempotency
  ↓
Lock authoritative state
  ↓
Validate conditions
  ↓
Decision
  ↓
Authorization
  ↓
Canonical Ledger mutation
  ↓
Escrow state transition
  ↓
Witness
  ↓
Transactional Outbox
  ↓
COMMIT
```

A failed transaction must not leave partial value movement.

Replay of the same transaction request must be idempotent.

Reuse of the same idempotency key with a different request fingerprint must fail.

---

## 7. Deep value-truth reconciliation

GerChain includes a read-only deep reconciliation mechanism:

`persistence/deep_value_reconciliation.py`

It checks the relationship among:

- canonical Ledger movement
- canonical Escrow
- Witness
- Outbox
- durable Idempotency evidence
- integrity hash

The core invariant is:

> **Balance equality ≠ Value-truth equality.**

A value movement is considered structurally reconciled only when its required authoritative evidence agrees.

For state-only operations such as LOCK, the reconciliation model explicitly permits:

```text
LOCK
→ Witness
→ Outbox
→ Idempotency
→ NO Ledger movement
```

This avoids falsely treating state-only operations as value movements.

---

## 8. Integrity model

Canonical movement evidence is bound to:

- transaction ID
- operation
- escrow ID
- source
- destination
- amount
- currency

An integrity hash is calculated from this canonical movement material.

The reconciliation process detects, among others:

- missing operation
- invalid amount
- missing escrow reference
- orphan escrow reference
- unwitnessed movement
- witness mismatch
- missing outbox
- outbox aggregate/type mismatch
- missing idempotency evidence
- incomplete idempotency
- missing integrity hash
- integrity hash mismatch
- orphan witness
- orphan outbox

---

## 9. Production runtime

The intended production construction path is:

```text
GERCHAIN_DATABASE_URL
        ↓
ProductionRuntimeConfig
        ↓
ProductionRuntimeFactory
        ↓
PostgreSQL engine
        ↓
Canonical persistence
        ↓
GerchainRuntime
        ↓
configure_canonical_ledger()
        ↓
require_canonical_ledger_authority()
```

The production entrypoint is:

`production_entrypoint.py`

The Docker production command uses this entrypoint rather than the legacy in-memory CLI.

Required production configuration includes:

- `GERCHAIN_DATABASE_URL`
- `GERCHAIN_ESCROW_ID`
- `GERCHAIN_ESCROW_AMOUNT`
- `GERCHAIN_CURRENCY`
- `GERCHAIN_WITNESS_ID`

### Important evidence rule

Source-code construction is **not** equivalent to production verification.

The presence of:

`runtime_mode == "production-postgresql"`

is not, by itself, production evidence.

Production readiness requires fresh exact-commit PostgreSQL execution evidence.

---

## 10. Production-readiness status

**Current status: IN PROGRESS / NOT LOCKED**

Implemented in source:

- canonical architecture boundary
- explicit adapter principle
- canonical Ledger transaction-aware mutation boundary
- canonical Ledger balance read
- canonical account creation boundary
- FUND → Canonical Ledger
- LOCK → durable Escrow boundary
- RELEASE → Canonical Ledger
- REFUND → Canonical Ledger
- CANCEL → Canonical Ledger
- SETTLEMENT → Canonical Ledger
- production runtime construction correction
- legacy value-authority freeze
- deep value-truth reconciliation
- idempotency/replay/conflict protections
- transaction-aware witness/outbox path
- fail-closed legacy mutation boundaries

### Remaining production gates

The following are **not yet claimed as GREEN** until fresh evidence exists:

1. real PostgreSQL boot
2. complete production schema/migration verification
3. full lifecycle PostgreSQL execution
4. recovery/restart verification
5. deep cross-store reconciliation on production PostgreSQL
6. production deployment/readiness semantics
7. exact-SHA CI evidence
8. independent re-performance
9. final production evidence package
10. production lock

---

## 11. Production lock rule

Production lock requires all critical conditions to be evidenced.

```text
ARCHITECTURE
     ↓
AUTHORITY
     ↓
TRANSACTION CORRECTNESS
     ↓
RECOVERY
     ↓
AUDITABILITY
     ↓
SECURITY / IAM
     ↓
OBSERVABILITY
     ↓
PERFORMANCE / STRESS
     ↓
DISASTER RECOVERY
     ↓
CI / RELEASE
     ↓
INDEPENDENT RE-PERFORMANCE
     ↓
FINAL EVIDENCE
     ↓
🔒 PRODUCTION LOCK
```

No single unit test, source-code inspection, or local success is sufficient to declare the complete infrastructure production-ready.

---

## 12. Key repository documents

| Document | Purpose |
|---|---|
| `docs/DEE_ARCHITECTURE_FREEZE.md` | Frozen canonical architecture |
| `docs/EA34_RUNTIME_VALUE_AUTHORITY_MAP.md` | Production value-authority map |
| `docs/EA34_LEGACY_VALUE_AUTHORITY_FREEZE.md` | Legacy authority freeze |
| `persistence/deep_value_reconciliation.py` | Deep value-truth reconciliation |
| `production_entrypoint.py` | Production runtime entrypoint |

---

## 13. Current production construction correction

The production construction path was corrected in:

`e860f502f3e1a2d56fd873ad2faab7b1ab630740`

The correction makes the entrypoint use the actual `ProductionRuntimeFactory` instance API and establishes Canonical Ledger configuration rather than the legacy Release authority.

This commit is **implementation evidence**, not production-readiness evidence.

---

## 14. Design principle

GerChain is built around a simple rule:

> **Найдвар дээр үнэ цэнэ хөдөлгөхгүй. Итгэл бий болсон нөхцөлд л үнэ цэнэ хөдөлнө.**

Structural trust is produced by the infrastructure itself through:

```text
Truth
+ Condition
+ Verification
+ Authority
+ Execution
+ Evidence
+ Recovery
= Structural Trust
```

The objective is not merely to automate transactions.

The objective is to establish a **durable, auditable, condition-aware and fail-closed infrastructure for digital economic value flow**.

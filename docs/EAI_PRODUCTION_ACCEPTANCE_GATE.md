# EAI — Escrow as Infrastructure: Production Acceptance Gate

**Status:** IN PROGRESS / NOT LOCKED  
**Branch:** `feat/ea21-transaction-aware-ledger`  
**Architecture authority:** `docs/DEE_ARCHITECTURE_FREEZE.md`  
**Scope:** Fundamental infrastructure + EAI. Product/application layers are excluded.

## 1. Canonical meaning

**EAI = Escrow as Infrastructure.** EAI is an architectural principle, not a new architecture layer, not G3 itself, not GerChain, not CORE, and not a second Escrow Engine.

- **G1:** Escrow as Tool
- **G2:** Escrow as Service
- **G3:** Escrow as Infrastructure — the escrow foundation that implements and governs EAI.
- **Canonical Ledger:** the only production authority for account balances and value movements.
- **Canonical Escrow Aggregate:** the only durable production escrow state machine.
- **Witness / Audit / Outbox:** distinct evidence and delivery responsibilities; none may become a second value authority or witness chain.

## 2. Non-negotiable invariants

1. One escrow aggregate → one durable escrow state machine.
2. One canonical ledger → one authoritative value-movement boundary.
3. No production value mutation outside `PostgreSQLAtomicLedger.transfer_in_transaction` or its approved transaction-aware boundary.
4. Decision → Authorization → Release is mandatory; no direct release.
5. Every value-moving operation must bind transaction ID, operation, escrow ID, source, destination, amount, currency, integrity hash, witness evidence, outbox evidence, and completed idempotency evidence.
6. Same idempotency key + same request fingerprint is a replay; same key + different fingerprint is a conflict.
7. Escrow transitions, ledger movement, witness, outbox, and idempotency completion must commit or roll back together.
8. State-only operations such as LOCK must not be falsely required to have a value movement; they must still have their required durable state and evidence.
9. Production startup must fail closed on non-PostgreSQL configuration or missing canonical authority. No silent fallback to `MoneyLedger`, `ReleaseAccount`, `AccountBalance`, or SQLite stores.
10. Recovery may not duplicate value movement. Failed verification remains HOLD.
11. Trust, Transparency, and Performance are machine-checkable release conditions, not narrative claims.
12. Balance equality alone is insufficient: **Balance equality ≠ Value-truth equality.**

## 3. Production acceptance gates

| Gate | Required evidence | Current disposition |
|---|---|---|
| A. Canonical construction | Factory uses the exact supported constructor and configures Canonical Ledger authority | Code correction committed; PostgreSQL boot still unverified |
| B. Schema/migrations | Versioned migration creates the complete escrow lifecycle, ledger, witness, outbox and idempotency schema on clean PostgreSQL | OPEN |
| C. Lifecycle atomicity | CREATE, FUND, LOCK, RELEASE, REFUND, CANCEL tested against PostgreSQL, including rollback and replay/conflict | Partially implemented; exact-SHA PostgreSQL evidence OPEN |
| D. Value-truth graph | Deep reconciliation passes for clean graph and detects each injected mismatch | Unit/integration coverage exists; production PostgreSQL re-performance OPEN |
| E. Legacy isolation | Legacy balance stores are read-only/non-authoritative or removed; no production bypass | Runtime fail-closed changes exist; physical freeze/migration evidence OPEN |
| F. Startup/readiness | Clean PostgreSQL boot, schema version validation, real readiness/health signal, controlled shutdown | OPEN |
| G. Recovery | Restart/recovery after abandoned processing; no duplicate movement; failed verification stays HOLD | OPEN pending production re-performance |
| H. Security/governance | IAM/MFA, privileged-access review, branch protection/ruleset evidence | OPEN; organizational evidence required |
| I. Exact-SHA CI | Required workflow results tied to the immutable candidate SHA | OPEN until required checks complete and are retained |
| J. Independent re-performance | Independent operator reruns the documented scenarios and preserves outputs | OPEN |

## 4. Required deep-reconciliation acceptance

The read-only reconciliation must verify both directions of the evidence graph:

`Canonical Ledger Movement ↔ Escrow Aggregate`  
`Canonical Ledger Movement ↔ Witness`  
`Canonical Ledger Movement ↔ Outbox event type + aggregate`  
`Canonical Ledger Movement ↔ completed idempotency record`  
`Canonical Ledger Movement ↔ integrity hash`

The report must contain zero unexplained issues. A passing test fixture is not evidence that a deployed PostgreSQL database is reconciled.

## 5. Release rule

EAI is **NOT production-ready** until every mandatory gate is either:
- closed with immutable, reproducible evidence tied to the same candidate SHA; or
- explicitly accepted as a documented exception by the accountable authority.

No status is promoted to GREEN from code presence alone. No product/application layer is introduced as part of this gate.

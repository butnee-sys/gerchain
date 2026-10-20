# GERCHAIN EAI — CONSOLIDATED FINAL LOCK REGISTER
Date: 2026-10-18
Repository: `butnee-sys/gerchain`
Working branch: `feat/ea21-transaction-aware-ledger`
Latest specifically confirmed correction commit: `e860f502f3e1a2d56fd873ad2faab7b1ab630740`

## 1. Lock decision

This register consolidates prior implementation and test evidence. A prior GREEN result remains GREEN as an evidence-backed component result; it is not relabeled yellow merely because another gate remains open. A prior YELLOW/OPEN item is marked GREEN only where the cited implementation and tests actually cover the requirement. Missing or unobserved external execution evidence is not fabricated.

**Architecture and canonical value-authority design: LOCKED.**
**EAI implementation scope and authority boundaries: LOCKED.**
**Whole production deployment / operational EAI: NOT YET FINAL-LOCKED** until the production PostgreSQL migration, boot, runtime exercise, and exact-commit CI/re-performance evidence are captured. This distinction prevents an architectural lock from being mistaken for a production certification.

## 2. Frozen architectural invariants

1. EAI means **Escrow as Infrastructure**. It is a principle, not an additional architecture layer, not G3 itself, not GerChain, not CORE, and not a second Escrow Engine.
2. G3 is the escrow foundation and governs Condition Policy, Escrow Policy, Governance Policy, and the Trinity: Trust + Transparency + Performance.
3. The canonical value authority is the Canonical Ledger: `gerchain_ledger_accounts` and `gerchain_ledger_movements`, through `PostgreSQLAtomicLedger` transaction-aware APIs.
4. One canonical escrow aggregate/state machine; one authoritative value-movement boundary; one witness path; one production outbox path.
5. Decision ≠ Authorization ≠ Release ≠ Settlement ≠ Reconciliation.
6. No direct release. Required order: Decision → Authorization → Release.
7. Unknown or unresolved required conditions do not pass; they HOLD or DENY.
8. No production value movement outside the Canonical Ledger mutation boundary.
9. Replay with the same request is idempotent; reuse with a different request fingerprint is a conflict.
10. Recovery must never duplicate value movement.
11. Balance equality alone does not prove value-truth equality.
12. Legacy stores and in-memory ledgers are non-authoritative in production and must not silently become fallback authorities.

## 3. Consolidated evidence matrix

Status interpretation:
- **GREEN — prior implementation/test evidence:** previously implemented and tested in repository evidence described below.
- **GREEN — code path implemented, runtime evidence pending:** code wiring exists, but real production PostgreSQL execution is not yet evidenced.
- **OPEN — external/operational evidence required:** cannot be closed from code inspection alone.

| Gate | Consolidated status | Evidence / limitation |
|---|---|---|
| Frozen canonical architecture and explicit adapter path | GREEN — LOCKED | `docs/DEE_ARCHITECTURE_FREEZE.md`, frozen SHA `0940d8aae8858d34604eb9d7174a8afc636bb2f` |
| Canonical Ledger transaction-aware mutation | GREEN — prior tests | EA-21 `transfer_in_transaction`: commit/replay/conflict/rollback tests previously recorded |
| Durable escrow lifecycle operations | GREEN — implementation and prior integration tests | CREATE still requires complete durable aggregate production-path confirmation; FUND/LOCK/RELEASE/REFUND/CANCEL implementations and runtime cutovers previously recorded |
| Canonical SETTLEMENT and READ | GREEN — implementation and prior tests | Settlement coordinator delegates to Canonical Ledger; balance read uses CanonicalLedgerRead |
| Legacy value authority freeze | GREEN — policy documented | `docs/EA34_LEGACY_VALUE_AUTHORITY_FREEZE.md`, commit `f81500c12aebd4956ca8e13776a0aef5a4c602a2`; physical deletion/read-only enforcement still needs deployment proof |
| Deep value-truth reconciliation | GREEN — code and prior test matrix | `persistence/deep_value_reconciliation.py`; movement ↔ escrow/witness/outbox/idempotency/integrity checks; LOCK correctly treated as state-only |
| Outbox movement-operation binding | GREEN — prior negative test | Outbox event type and aggregate must match movement operation/escrow; mismatch test recorded at `97c937c9ee9841314388e253af49f952e4fc5b00` |
| State-only LOCK idempotency handling | GREEN — prior regression test | Avoids false orphan-idempotency findings where schema does not encode operation type; latest recorded correction `77a78e8c92b6564aa4ac9290b4db4810b5cdd0e5` |
| Production entrypoint construction | GREEN — corrected in source; runtime pending | `production_entrypoint.py` now instantiates `ProductionRuntimeFactory(ProductionRuntimeConfig(...))` and calls instance `create()`; correction commit `e860f502f3e1a2d56fd873ad2faab7b1ab630740` |
| Factory uses canonical Ledger authority | GREEN — corrected in source; runtime pending | Factory initializes canonical persistence metadata and calls `configure_canonical_ledger` / `require_canonical_ledger_authority`; not evidence that all production schema migrations are complete |
| PostgreSQL migration completeness and schema compatibility | OPEN | `metadata.create_all` is not a versioned migration system; full canonical schema and upgrade path need actual PostgreSQL verification |
| Production PostgreSQL boot and lifecycle run | OPEN | No fresh exact-commit execution evidence surfaced in this consolidation |
| Exact-SHA CI result | OPEN / UNVERIFIED | Earlier checks reported `[]`; this means no verifiable check result, not GREEN |
| IAM/MFA and privileged-access review | OPEN | Previously listed as missing; no new evidence supplied in this register |
| Independent re-performance / external assurance | OPEN | Must be performed and recorded; repository tests are not independent attestation |
| Production health/readiness, restart and recovery exercise | OPEN | Entrypoint loop alone is not a readiness/health contract or proof of recovery correctness |

## 4. Canonical transaction invariant

For every value-moving operation, the intended atomic unit is:

`BEGIN → lock idempotency/escrow/accounts → validate → mutate Canonical Ledger → transition canonical escrow → append witness → append outbox → complete durable idempotency → COMMIT`

All writes participating in that unit must use the same database session/transaction. External outbox delivery occurs after commit and must use lease/recovery semantics. No secondary balance store may independently authorize or mutate value.

## 5. EAI acceptance contract

EAI is accepted as an architectural/implementation contract only when:
- asset and escrow truth are authoritative and non-duplicated;
- condition, decision, authorization, release, settlement, and reconciliation boundaries remain separate;
- all value-moving operations route through Canonical Ledger;
- every committed movement has matching escrow reference, witness, outbox, durable idempotency, and integrity evidence;
- state-only operations such as LOCK are reconciled according to their own operation semantics;
- replay, conflict, rollback, and abandoned-processing recovery cannot duplicate value;
- legacy runtime paths fail closed and cannot silently regain authority.

The first six bullets have implementation and prior test evidence recorded in the project history. Legacy physical retirement, PostgreSQL deployment proof, operational recovery, IAM/MFA, and independent re-performance remain separate release gates.

## 6. Final lock boundary

**LOCKED NOW**
- canonical architecture;
- EAI meaning and scope;
- canonical value-authority decision;
- operation boundaries and transaction invariants;
- deep reconciliation contract and previously tested code paths;
- production entrypoint/factory source correction.

**NOT CLAIMED GREEN**
- production PostgreSQL migration and boot;
- exact-commit CI;
- real production lifecycle/restart/recovery evidence;
- IAM/MFA and privileged-access review;
- independent re-performance.

No architecture redesign is permitted during remaining verification. Any proposed change to the frozen architecture requires an explicit architecture-change proposal and approval. Remaining work is verification, evidence capture, and operational hardening—not reopening the canonical design.

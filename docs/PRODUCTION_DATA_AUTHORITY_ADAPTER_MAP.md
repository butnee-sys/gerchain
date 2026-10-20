# Production Readiness — Canonical Data, Authority and Adapter Map

Status: EVIDENCE MAP / NOT A LOCK DECISION
Scope: Fundamental architecture + EAI; product-layer functionality is excluded.
Branch: `feat/ea21-transaction-aware-ledger`
Canonical architecture: `docs/DEE_ARCHITECTURE_FREEZE.md`

## 1. Canonical layer path

```text
DE
→ DE Adapter
→ DEE
→ DEE ↔ G-3 Adapter
→ G-3 Escrow Foundation
→ G-3 ↔ CORE Adapter
→ NEF + GerChain Core Infrastructure
→ CORE ↔ EXIM Adapter
→ EXIM Port
→ EXIM ↔ I2B Adapter
→ I2B
→ I2B ↔ Multi-Connector Adapter
→ State / Company / Person
→ Digital Economy Activities
```

This is the frozen architecture contract, not a claim that every adapter has passed production deployment tests. Each edge must have a named contract, authorization propagation, input validation, failure semantics and test evidence.

## 2. Authoritative truth and persistence inventory

| Data / truth | Canonical authority | Candidate durable PostgreSQL representation | Legacy / non-authoritative stores or paths | Required proof |
|---|---|---|---|---|
| Asset registration, valuation, verification | NEF | NEF adapter/port persistence; exact production table inventory must be confirmed from deployed schema | In-memory NEFStateEngine in `network/api_server.py` and `node_cli.py` | NEF-to-GerChain adapter contract; versioned asset truth and stale-version rejection |
| Current account balance | Canonical Ledger | `gerchain_ledger_accounts` | `ReleaseAccount`, `AccountBalance`, `MoneyLedger`, SQLite account balances, application-owned balance fields | All production mutations route through transaction-aware Ledger; reconciliation across legacy stores |
| Value movement history | Canonical Ledger | `gerchain_ledger_movements` | `SettlementMovement` and legacy release movement tables must not be authoritative | Unique transaction identity, source/destination/amount/currency/operation/escrow binding and integrity hash |
| Escrow aggregate and state machine | Canonical Escrow aggregate | `escrows` | `ReleaseEscrow`, in-memory `EscrowEngine`, SQLite escrow state | Durable full lifecycle, version/transition checks, no parallel authoritative state |
| Witness execution evidence | One authoritative Witness path | `gerchain_transaction_witnesses` | `ReleaseWitness`, in-memory witness chain unless explicitly test-only | Witness-to-movement binding; mismatch and orphan tests |
| Audit trail | Audit authority defined by frozen policy; distinct from Witness | Deployed audit table/schema must be explicitly inventoried before lock | Application logs alone are not an authoritative audit trail | Who/what/when/why, append-only/tamper evidence, correlation to transaction |
| Outbox delivery intent | One production Outbox | `gerchain_outbox_events` | Any second outbox representation (including `outbox`) must be classified and frozen | Same DB transaction as state/value/witness/idempotency; type and aggregate match; delivery lease/recovery |
| Idempotency | Durable idempotency boundary | `gerchain_idempotency_records` | `core.idempotency.IdempotencyEngine` in-memory dictionary | Same key + same fingerprint replays; different fingerprint conflicts; no second value movement |
| Migration history | Canonical migration chain | `schema_version` | Manual DDL / `create_all` as a substitute for upgrades | Exact versions 1–17, checksum agreement, concurrency serialization, rerun stability |
| External-system boundary | EXIM Port | Boundary adapter contract; database not itself an authority | Direct calls into core implementation from downstream systems | Deny bypass; authenticated, validated, authorized requests only |
| Business access | I2B gateway | No parallel core truth | Direct downstream database mutation | Only controlled interfaces may request services; no direct core mutation |

**Important limitation:** this table is a repository-level inventory. NEF production table names, audit persistence, all deployed database instances, and the production legacy-store inventory must be established from actual deployment configuration and database catalogs. Unknown inventory is an open gate, not a pass.

## 3. Authority and adapter invariants

1. NEF owns authoritative asset registration/valuation/verification truth.
2. Canonical Ledger owns production balances and value movement history.
3. Canonical Escrow owns the durable escrow aggregate/state machine.
4. G-3 owns conditions, escrow policy and governance policy; it is not a second operational engine.
5. GerChain executes canonical operational value movement; no production mutation bypasses its transaction boundary.
6. Witness proves execution facts; Audit records accountability and must not be treated as the same store/role.
7. One authoritative Outbox and one durable idempotency boundary per production flow.
8. Every frozen layer edge uses its explicit adapter; no downstream component can mutate PDEIZ truth, authority, policy or core execution state directly.
9. Release sequence is Decision → Authorization → Release. Unknown or unresolved required conditions fail closed.
10. Recovery must not duplicate value movement; failed verification remains HOLD.

## 4. Value-truth reconciliation contract

A balance comparison alone is insufficient. For each value-moving transaction, reconcile the graph:

```text
Canonical Ledger Movement
  ↔ transaction_id + operation + escrow_id
  ↔ Canonical Escrow state/version
  ↔ Witness evidence
  ↔ Audit record
  ↔ Outbox event type + aggregate
  ↔ durable Idempotency key + request fingerprint + result
  ↔ integrity hash
```

Required negative cases include missing/orphan witness, wrong witness binding, missing/wrong outbox, missing idempotency, incomplete idempotency, wrong fingerprint replay, duplicate movement, mismatched integrity hash, unauthorized transition, rollback after injected failure, restart/recovery after abandoned processing, and re-run after a committed transaction.

## 5. Gate-to-evidence contract

The final master gate must use an exact commit SHA and must never infer an architecture gate's success from a PostgreSQL smoke test alone. Every gate record must contain:
- outcome: `success`, `open`, `failure`, or `not_applicable`;
- an evidence URI or artifact path;
- the same exact commit SHA;
- test/workflow identifier and result where applicable;
- explicit limitations and owner for open items.

A documentary map is not by itself proof that an operational control works. IAM/MFA, privileged-access review, observability, performance/stress, disaster recovery, main-branch governance, and independent re-performance remain OPEN until supported by actual, reviewable evidence.

## 6. Current decision

**NOT LOCKED.** This file documents the canonical map and proof obligations; it does not declare production readiness. The master gate's machine-generated decision and exact-SHA evidence bundle remain authoritative.

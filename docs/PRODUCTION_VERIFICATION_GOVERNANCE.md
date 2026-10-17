# Production Verification Governance — Canonical Gate v1

Status: FROZEN VERIFICATION POLICY — 2026-10-05

## 1. Scope

This verification policy applies only to the fundamental Digital Economy infrastructure and EAI (Escrow as Infrastructure).

SHUUD is explicitly OUT OF SCOPE for the fundamental infrastructure production gate.

SHUUD is a separate application layer and must be verified by its own isolated test/sandbox workflows.

## 2. One authoritative production gate

The authoritative production verification gate is:

`.github/workflows/production-postgresql-gate.yml`

It is the single release gate for:
- PostgreSQL production construction
- canonical schema completeness
- Canonical Ledger authority
- transaction-aware value movement
- deep value-truth reconciliation
- EAI production re-performance
- SHUUD isolation boundary tests

Other PostgreSQL production workflows are evidence/re-performance helpers only and must not be interpreted as additional independent GREEN gates.

## 3. Authority rules

A result is authoritative only when:
1. it identifies the exact tested commit SHA;
2. it executes against real PostgreSQL;
3. the canonical gate completes successfully;
4. no required sub-gate is skipped;
5. the result is not merely a duplicate run of the same evidence.

GREEN means verified evidence for that exact SHA. UNVERIFIED means no claim.

## 4. SHUUD separation invariant

SHUUD is not part of the fundamental infrastructure architecture.

Required boundary:

SHUUD
→ EXIM Port / published boundary
→ fundamental infrastructure

Forbidden:
- direct SHUUD import of GerChain core modules;
- SHUUD dependency on canonical services namespace;
- SHUUD re-entry through legacy integration;
- SHUUD ownership of Ledger, Money, Escrow, Witness, Decision, Authorization, Release or Settlement authority.

The existing `tests/test_shuud_exim_boundary.py` is the authoritative code-level isolation test.

The SHUUD sandbox is separately composed under `sandbox/docker-compose.yml` and starts `shuud.server:app`; it is not the production GerChain entrypoint.

## 5. Duplicate-check prevention

Do not create a new production gate for an already-covered invariant.

Before adding a check:
1. identify the canonical gate;
2. identify the invariant it proves;
3. reuse the existing test where possible;
4. add a new test only when it proves a genuinely distinct invariant;
5. update this governance document if a new authoritative gate is required.

A workflow may be retained for independent re-performance, but its result must not be represented as a second production authority.

## 6. Production authority

The only production value authority is:

- `gerchain_ledger_accounts`
- `gerchain_ledger_movements`
- `PostgreSQLAtomicLedger.transfer_in_transaction`

Legacy value stores remain non-authoritative and must fail closed.

## 7. Lock rule

No architecture or production lock may be declared solely from:
- unit tests;
- duplicate workflow success;
- stale evidence;
- documentation claims;
- local execution;
- SHUUD sandbox success.

Final lock requires exact-SHA canonical PostgreSQL evidence plus the remaining organizational/independent assurance gates.

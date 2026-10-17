# PRODUCTION READY — MASTER WORK PLAN v1.0
## FINAL LOCK Readiness Dossier

**Assessment date:** 2026-10-14  
**Repository:** `butnee-sys/gerchain`  
**Branch:** `feat/ea21-transaction-aware-ledger`  
**Exact branch tip reviewed:** `cd5cf0ba1a99c743e06ff2ea75ba16fe9da5cb10`  
**Disposition:** **FINAL LOCK PREPARED — NOT LOCKED**

This dossier consolidates implementation and CI evidence and records the remaining release blockers. It is not a production approval or a substitute for a signed, authorized lock decision.

## 1. Scope and frozen architecture

The target is the **whole foundational architecture plus EAI (Escrow as Infrastructure)**, not CORE alone. CORE is one infrastructure/sub-infrastructure. SHUUD/SHIID and other product-layer work remain outside this lock and must not be used to imply foundational readiness.

Canonical frozen architecture reference:
- `docs/DEE_ARCHITECTURE_FREEZE.md`
- Frozen blob: `0940d8aae8858d34604eb9d7174a8afc636bb2f`

EAI is an architectural principle, not a new layer, not G3 itself, and not a second Escrow Engine. G3 governs escrow conditions and the Trust + Transparency + Performance trinity. GerChain remains the operational value-flow infrastructure; NEF remains authoritative for asset registration, valuation, and verification truth.

## 2. Production authority and hard invariants

Canonical production value authority:
- `gerchain_ledger_accounts` — authoritative balance state
- `gerchain_ledger_movements` — authoritative movement evidence
- `PostgreSQLAtomicLedger.transfer_in_transaction` — transaction-aware mutation boundary
- `CanonicalLedgerRead` — authoritative balance read
- Canonical Escrow aggregate — durable escrow state machine
- One Witness path, one authoritative Outbox path, durable idempotency

Required transaction invariant:
**Ledger movement + escrow transition + witness + outbox + durable idempotency must commit or roll back as one database transaction.**

Required trust invariant:
**Decision → Authorization → Release**; unresolved required conditions fail closed.

Required recovery invariant:
**DETECT → ISOLATE → HOLD → DIAGNOSE → RECONCILE → RECOVER → VERIFY → AUDIT**. Failed verification remains HOLD; recovery cannot create an alternate truth authority.

PDEIZ protection invariant:
**NO DOWNSTREAM ACTOR MAY ALTER THE AUTHORITATIVE TRUTH, AUTHORITY, POLICY, OR CORE EXECUTION STATE OF PDEIZ DIRECTLY.**

## 3. Implemented work and retained evidence

The following are implementation/evidence claims only to the degree explicitly supported by the repository and retained run records:

- Canonical Ledger transaction-aware transfer boundary and durable replay/conflict behavior.
- Canonical durable Escrow paths for FUND, LOCK, RELEASE, REFUND, CANCEL, READ; settlement delegated to the Canonical Ledger.
- Canonical balance/account read/write paths.
- Deep value-truth reconciliation across movement, escrow, witness, outbox, idempotency, and integrity hash; state-only LOCK is not falsely required to have a Ledger movement.
- Legacy direct mutation paths identified in API/UI have fail-closed behavior; legacy SQLite/in-memory stores are not production authority.
- Production entrypoint/factory now apply the canonical migration registry, validate canonical PostgreSQL schema, and require Canonical Ledger authority.
- The latest branch tip contains a fix for canonical migration retry evidence, commit `cd5cf0ba1a99c743e06ff2ea75ba16fe9da5cb10`.

Historical successful evidence is retained in `docs/EA34_RUNTIME_VALUE_AUTHORITY_AUDIT.md`, including exact PostgreSQL/EAI/independent evidence on prior branch tip `f11fcb6411f1458c7bb4696566a695a52141b0c3`. That historical success does **not** override current exact-tip failures.

## 4. Exact branch-tip CI inspection — 2026-10-14

Branch tip: `cd5cf0ba1a99c743e06ff2ea75ba16fe9da5cb10`.

Observed commit-associated workflow runs:
- Canonical PostgreSQL Migration Gate — run `38535210671` — **SUCCESS**
- PostgreSQL migration idempotency — run `38535210629` — **SUCCESS**
- CodeQL Advanced — run `38535210653` — **SUCCESS**
- DEE Security Gate — run `38535210639` — **SUCCESS**
- CORE Operating Reconciliation — run `38535210645` — **SUCCESS**
- Production PostgreSQL Gate — run `38535210647` — **FAILURE**
- FINAL EAI/CORE Exact-SHA Gate — run `38535210731` — **FAILURE**
- EAI PostgreSQL Re-performance — run `38535210652` — **FAILURE**
- PostgreSQL Migration and Production Proof — run `38535210615` — **FAILURE**
- PostgreSQL migration gate — run `38535210781` — **FAILURE**
- PostgreSQL Production Re-performance — run `38535210622` — **FAILURE**
- Production Gate — run `38535210769` — **FAILURE**
- `core-gates` — run `38535210625` — **FAILURE**

The commit combined-status endpoint reported only Snyk success; it does not establish an overall green commit.

### Failure signatures observed in job logs

1. Canonical production schema guard rejects PostgreSQL's actual CHECK expression rendering:
   - expected fragment `>0`, actual `check((amount>(0)::numeric))`
   - expected fragment `is not null`, actual `check((length((integrity_hash)::text)=64))`
   This is a schema-guard semantic-normalization defect to fix and re-test against PostgreSQL 16, not to bypass by weakening the invariant.

2. Migration concurrency tests in older integration paths still invoke standalone migration execution, while the repository now intentionally disables standalone migration execution in favor of the canonical migration chain. These tests/entrypoints must be aligned with the one canonical migration runner and re-performed.

3. Production Gate output includes duplicate-key errors from the legacy `gerchain_release_operations` idempotency path. The canonical production path must be confirmed not to depend on this legacy release authority; any legacy concurrency gate must be isolated from production readiness or corrected so it tests the intended boundary without hiding a real defect.

4. Broad `core-gates` currently includes product-layer SHUUD failures (22 failed, 897 passed, 50 skipped in the observed run). Those failures must be reported separately from the foundational/EAI lock; they must not be silently ignored, but neither should product-layer tests be used as evidence that the canonical EAI boundary itself passed or failed without scope attribution.

## 5. Lock gate matrix

| Gate | Current disposition | Evidence / closure requirement |
|---|---|---|
| Canonical architecture reference | FROZEN | Exact frozen document/blob exists |
| Canonical Ledger authority design and runtime paths | IMPLEMENTED; exact-tip re-verification required | Pass exact-SHA production tests |
| PostgreSQL migration registry | PARTIAL PASS | Migration gate and idempotency run pass; production schema guard currently fails |
| PostgreSQL production boot | BLOCKED | Fix CHECK normalization; rerun exact-tip boot/schema gate |
| FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT | HISTORICAL PASS; CURRENT TIP NOT GREEN | Re-perform on current exact SHA and retain artifacts |
| Deep value-truth reconciliation | IMPLEMENTED; CURRENT TIP NOT GREEN | Exact-SHA PostgreSQL test must pass |
| Durable replay/idempotency | IMPLEMENTED; broader legacy gate fails | Demonstrate single movement under same-key concurrency on canonical path |
| Legacy authority freeze/removal | OPEN | Inventory, read-only freeze, migration/reconciliation, approved archive/removal, re-performance |
| IAM/MFA and privileged access | MISSING / OPEN | Organizational evidence and privileged-access review |
| Main branch protection/review governance | UNVERIFIED / OPEN | Verify branch rules, required checks, review policy |
| Independent architecture/oracle review | OPEN | Independent reviewer reproduces results against immutable SHA and retained artifacts |
| Evidence index and signed lock decision | OPEN | Update evidence index/control matrix and obtain authorized approval |

## 6. Mandatory closure sequence

1. Correct CHECK-constraint semantic normalization so valid PostgreSQL 16 expression renderings pass while genuinely weakened/missing constraints still fail.
2. Align migration concurrency/idempotency tests with the canonical migration runner; remove stale alternate migration invocation paths.
3. Isolate and correct legacy release-operation concurrency checks; do not let legacy release tables act as production authority.
4. Run the complete canonical PostgreSQL gate on the exact new commit.
5. Require all foundational/EAI jobs to succeed on the same exact SHA; collect workflow run IDs, job logs, artifacts, migration manifest/checksums, schema inspection, and deep reconciliation output.
6. Re-perform CREATE/FUND/LOCK/RELEASE/REFUND/CANCEL/SETTLEMENT, replay/conflict, rollback, restart/recovery, and migration-upgrade tests against PostgreSQL 16.
7. Close legacy value-store freeze/removal/archive with before/after reconciliation evidence.
8. Close IAM/MFA, privileged-access review, branch governance, and independent review—or record explicit authorized audit exceptions.
9. Update evidence index/control matrix to reference the exact release SHA and artifacts.
10. Only then issue a separate FINAL LOCK record approved by the responsible authority.

## 7. Final decision

**DO NOT DECLARE FINAL LOCK on branch tip `cd5cf0ba1a99c743e06ff2ea75ba16fe9da5cb10`.**

Reason: exact-tip production/EAI/CORE workflows currently fail, including a reproducible PostgreSQL CHECK-definition mismatch and migration/legacy idempotency gate issues. Successful migration-registry and security workflows are positive partial evidence, not sufficient proof of end-to-end production readiness.

**Current status: FINAL LOCK PREPARED — NOT LOCKED.**  
No product-layer expansion is authorized by this dossier. No gate may be marked GREEN without fresh exact-SHA evidence.

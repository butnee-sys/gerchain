# GERCHAIN EAI — PRODUCTION READY FINAL LOCK RECORD

**Record date:** 2026-10-18  
**Repository:** `butnee-sys/gerchain`  
**Working branch:** `feat/ea21-transaction-aware-ledger`  
**Record type:** Evidence consolidation and scoped lock  
**Disposition:** **VERIFIED SUB-GATES LOCKED; OVERALL PRODUCTION RELEASE NOT YET LOCKED**

## 1. Purpose and lock rule

This record consolidates previously verified GREEN evidence for GerChain EAI and locks those specific gates against casual reopening. It does not promote unverified, partial, historical, or organizational controls to GREEN.

**A gate is GREEN only for the exact commit/run on which its evidence was produced.** Evidence from an older SHA is retained as valid historical execution evidence, but it does not automatically prove the current branch tip.

## 2. Locked GREEN evidence

The following evidence was recorded in `docs/EA34_RUNTIME_VALUE_AUTHORITY_AUDIT.md` under EA-35.28 and earlier evidence entries.

| Gate | Evidence anchor | Locked disposition |
|---|---|---|
| Real PostgreSQL 16 runtime boot | Commit `f11fcb6411f1458c7bb4696566a695a52141b0c3`; run `37463305181`; job `112267996297` | **GREEN — recorded execution SHA only** |
| Production PostgreSQL gate | Run `37463305107`; job `112268002110` | **GREEN — recorded execution SHA only** |
| EAI PostgreSQL Production Proof | Run `37463304934` | **GREEN — recorded execution SHA only** |
| Independent PostgreSQL persisted-value evidence | Run `37463304855`; job `112267995003` | **GREEN — recorded execution SHA only** |
| CORE Operating Reconciliation | Run `37463305050` | **GREEN — recorded execution SHA only** |
| CodeQL Advanced | Run `37463304876` | **GREEN — recorded execution SHA only** |
| Snyk external security check | Combined status on the recorded evidence SHA; Snyk result retained in the audit record | **GREEN — recorded execution SHA only** |
| Deep value-truth reconciliation | Included in the successful PostgreSQL production gate and independent persisted-value verification | **GREEN — recorded execution SHA only** |
| FUND / LOCK / RELEASE / REFUND / CANCEL / SETTLEMENT value-flow | Included in the successful PostgreSQL production gate | **GREEN — recorded execution SHA only** |
| Canonical Ledger authority and production entrypoint boot | Included in the successful PostgreSQL production gate | **GREEN — recorded execution SHA only** |

Supporting source record: [EA34 Runtime Value Authority Audit](https://github.com/butnee-sys/gerchain/blob/feat/ea21-transaction-aware-ledger/docs/EA34_RUNTIME_VALUE_AUTHORITY_AUDIT.md).

The earlier PostgreSQL runtime-construction test also recorded a real PostgreSQL 16 service, exact execution SHA `f158316277d65234e355b6040a905884ee4f4adf`, run `37002917360`, job `production-postgresql`, conclusion `success`, and one passing production re-performance test. That evidence remains locked to that execution SHA.

## 3. Canonical invariants now recorded as locked

1. `gerchain_ledger_accounts` and `gerchain_ledger_movements` are the production Canonical Ledger authority.
2. Production value movement uses the transaction-aware Canonical Ledger boundary.
3. FUND, RELEASE, REFUND, funded CANCEL reversal, and SETTLEMENT must not mutate value through a second balance authority.
4. LOCK is a durable escrow-state transition and does not fabricate a Ledger movement.
5. Refund destination and cancellation reversal destination come from authoritative escrow data, not an untrusted caller-supplied destination.
6. Witness, outbox, durable idempotency, and escrow transition evidence must reconcile with each value movement.
7. Replaying the same operation must not duplicate value movement; conflicting reuse must fail closed.
8. Legacy direct-mutation endpoints previously identified in the audit record are fail-closed and must not be treated as production value paths.
9. No evidence in this record authorizes a second authoritative Ledger, Witness Chain, Escrow Engine, or application-owned value truth.

## 4. Explicitly NOT GREEN / release blockers

The following items are **not** closed by this record:

- A single current branch-tip SHA with all required CI, migration, process-restart/recovery, and independent verification gates successful together.
- Full process-kill + PostgreSQL restart + recovery + replay proof on that same exact SHA.
- Confirmation that versioned migrations upgrade the actual starting schema of the target production database, not only a fresh PostgreSQL instance.
- Physical removal or independently verified archival of legacy value stores and duplicate persistence surfaces.
- Organizational IAM/MFA and privileged-access review evidence.
- Main-branch protection and release-governance evidence.
- Final independent architecture/oracle assurance package.
- A fresh successful full required-workflow set for the current branch tip. The current record commit itself has no retrieved successful combined-check evidence attached.

These are release blockers, not reasons to erase the already-proven sub-gates. Keep the verified PostgreSQL/EAI sub-gates closed while the remaining gates are completed.

## 5. Final disposition

**CLOSED / LOCKED**
- Historical exact-SHA PostgreSQL production runtime and value-flow evidence.
- Historical exact-SHA EAI PostgreSQL proof.
- Historical exact-SHA independent persisted-value verification.
- Historical exact-SHA deep value-truth reconciliation.
- Historical exact-SHA Operating Reconciliation, CodeQL, and Snyk evidence.
- Canonical value-authority and reconciliation invariants listed in Section 3.

**OPEN / NOT LOCKED**
- Overall `GERCHAIN EAI PRODUCTION READY` release declaration.
- Current-tip unified CI and independent re-performance.
- Production-starting-schema migration compatibility.
- Full restart/recovery proof on one exact SHA.
- Legacy-store retirement and organizational governance controls.

**Final ruling:** The verified GREEN items are consolidated and locked as scoped evidence. The repository is **not declared fully production-ready** until every release blocker in Section 4 is supported by fresh, exact-SHA evidence and formally closed. This distinction preserves the truth of prior successful tests without turning historical evidence into an unsupported current release claim.

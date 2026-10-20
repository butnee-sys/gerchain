# FINAL LOCK — EA-35 PostgreSQL Production Verification Gate

Status: **FINAL LOCK — CLOSED / VERIFIED**
Scope: EA-35 Canonical PostgreSQL production runtime, EAI production re-performance, and deep value-truth verification.
Branch at recorded historical verification: `feat/ea21-transaction-aware-ledger`
Verified candidate SHA: `f11fcb6411f1458c7bb4696566a695a52141b0c3`

## 1. Final decision

The EA-35 PostgreSQL production verification gate is **CLOSED**. It must not be reset to OPEN or described as incomplete merely because later commits exist or because a later review is performed.

The recorded exact-SHA evidence for the candidate above includes:
- `production-postgres` — run `37463305181` — SUCCESS
- `production-postgresql-gate` — run `37463305107` — SUCCESS
- `EAI PostgreSQL Production Proof` — run `37463304934` — SUCCESS
- `independent-postgresql-evidence` — run `37463304855` — SUCCESS
- `CORE Operating Reconciliation` — run `37463305050` — SUCCESS
- `CodeQL Advanced` — run `37463304876` — SUCCESS

Recorded production job `112267996297` completed migration/boot verification, production value-flow verification, and deep value-truth verification. Gate job `112268002110` completed syntax, canonical persistence, production entrypoint, deep reconciliation, EAI production re-performance, and real PostgreSQL value-flow checks. Independent persisted-value verification job `112267995003` succeeded.

Evidence source: `docs/EA34_RUNTIME_VALUE_AUTHORITY_AUDIT.md`, section “EA-35.28 — Exact branch-tip production verification — 2026-10-06”.

## 2. Locked technical scope

The following scope is recorded CLOSED for the verified SHA:
1. PostgreSQL production runtime and migration/boot gate.
2. Canonical Ledger authority establishment.
3. Canonical escrow value-flow verification covered by the workflow.
4. Deep value-truth reconciliation.
5. EAI PostgreSQL production proof.
6. Independent persisted-value verification.

Historical evidence remains valid for the SHA and scope it actually tested. It is not deleted or relabeled as a failure by subsequent commits.

## 3. Change-control rule

A later commit does **not** reopen this gate by default.

Reopening is allowed only through a documented, evidence-based change-control record that states:
- the exact later SHA;
- the specific changed code/schema/configuration affecting this gate;
- the failed invariant or concrete regression;
- the new failing evidence;
- the narrow scope being reopened.

A request to “verify again”, a stale status paragraph, a missing status API result, or a newer documentation commit is not by itself a reopening trigger.

Any new candidate SHA that has not itself been tested must be labelled **NOT YET VERIFIED ON THAT SHA**; this does not erase or downgrade the locked historical gate.

## 4. Boundary: this is not an unsupported blanket architecture attestation

This lock closes the **EA-35 PostgreSQL production verification gate** on the recorded SHA. It does not silently certify separate organizational controls that are explicitly outside that evidence, including IAM/MFA governance, main-branch protection, formal organizational acceptance of legacy-store disposition, or independent architecture review.

Those are separate controls and must be tracked separately. They must not be used to reopen this already-closed PostgreSQL/EAI gate.

## 5. Canonical status vocabulary

- **CLOSED / VERIFIED** — this EA-35 gate, on the exact SHA and evidence listed above.
- **NEW SHA NOT YET VERIFIED** — only for later candidate code not covered by that evidence.
- **SEPARATE OPEN CONTROL** — a different governance or architecture assurance item; never a reason to relabel this gate as failed.
- **REOPENED** — permitted only by the evidence-based change-control rule in section 3.

## 6. Final lock statement

**EA-35 PostgreSQL production verification: FINAL LOCK — CLOSED / VERIFIED.**

The prior green evidence is retained. The gate will not be reopened through conversational repetition or status wording drift. Any future work must start from this locked record and identify a specific change or independent control, rather than restarting the verification cycle.

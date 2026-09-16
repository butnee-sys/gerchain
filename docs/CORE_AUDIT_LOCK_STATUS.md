# GerChain CORE — Audit Lock Status

**Document status:** Working audit record
**Scope:** GerChain CORE only
**SHUUD:** Explicitly out of CORE assurance scope
**Frozen PwC baseline:** `274f45c83ce088e2229a2628e3a80403a68503df`
**Main baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`
**Current CORE revalidation/evidence commit:** `3654060db520e5493c23a6203c6ab29eef60f314`

## 1. Purpose

This document establishes the controlled working state of the GerChain CORE audit evidence package. It does **not** declare final CORE LOCK. A control is marked GREEN/CLOSED only when supporting evidence is independently identifiable and retained.

## 2. Current disposition

| Control / area | Status | Basis |
|---|---|---|
| Atomic release / idempotency | GREEN | CORE test and PostgreSQL evidence retained |
| PostgreSQL concurrency | GREEN | CORE-only PostgreSQL workflow and successful current revalidation |
| `GC-RES-003` abandoned PROCESSING recovery | GREEN | Recovery implementation + dedicated tests |
| Operating reconciliation | GREEN | Current dedicated workflow success |
| CORE/SHUUD scope boundary | GREEN | CORE-only scope evidence |
| DEE cryptographic/security controls | GREEN | Current security evidence |
| CodeQL | GREEN | Successful run `35124770618` on current CORE revalidation commit |
| Snyk | GREEN | Successful current status |
| PwC evidence baseline | FROZEN | Baseline SHA retained without promotion |
| W3 schema/version authority | GREEN (bounded) | Current evidence package + `core-gates` run `35124770628`; independent PostgreSQL re-performance passed |
| IAM / MFA organizational evidence (`GC-IDM-001/002`) | MISSING | Organizational MFA, privileged-access and review evidence not independently retained |
| Privileged access review | MISSING | Organizational access inventory/review records not independently retained |
| Main branch governance | UNVERIFIED | Administrative branch protection/ruleset evidence still required |
| Post-merge main CI | NOT APPLICABLE TO CURRENT PR HEAD | Current CORE evidence is on unmerged PR head; final main-branch evidence must be obtained after merge |
| W3 complete production DDL migration execution | OPEN ARCHITECTURAL CONCERN | W3 currently validates schema/version authority and transition semantics; migration executor assurance remains separately defined |

## 3. Current technical state

The current CORE revalidation commit `3654060db520e5493c23a6203c6ab29eef60f314` has successful CORE gates, PostgreSQL concurrency, operating reconciliation, CodeQL and Snyk evidence. PR #82 remains open and draft; therefore this commit is **not yet the main branch** and must not be represented as such.

## 4. Lock rule

The CORE implementation may be treated as a **technical revalidation baseline**, but formal audit LOCK is not declared until the remaining governance/evidence gaps are either closed or explicitly accepted as audit exceptions by the responsible authority, the final audited commit is fixed, and the final assurance package is reconciled.

## 5. Non-negotiable audit principles

1. Source-code presence is not organizational control evidence.
2. A test PASS is not evidence that an organizational policy exists.
3. SHUUD is not included in CORE control conclusions.
4. Frozen PwC documents are not silently rewritten to claim later evidence.
5. Every final conclusion must identify the exact audited commit or retained evidence artifact.
6. Ambiguous states remain OPEN/MISSING rather than being promoted to PASS.
7. A PR head is not main-branch evidence until it is actually merged and the resulting main commit is revalidated.

## 6. Next closure sequence

1. Close the W3 PR only after review/approval of the bounded W3 evidence.
2. Re-run and retain all CORE assurance checks on the resulting main commit.
3. Complete organizational IAM/MFA and privileged-access evidence.
4. Resolve main branch protection/ruleset governance evidence.
5. Resolve or explicitly disposition the W3 migration-executor boundary.
6. Produce final G1–G90 closure matrix and residual-unknown register.
7. Produce final immutable-SHA CORE LOCK record.
8. Only after CORE LOCK, resume SHUUD work.

# GerChain CORE — Audit Lock Status

**Document status:** Working audit record
**Scope:** GerChain CORE only
**SHUUD:** Explicitly out of CORE assurance scope
**Frozen PwC baseline:** `274f45c83ce088e2229a2628e3a80403a68503df`
**Main baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`
**Current CORE revalidation/evidence commit:** `f7846aca4fb37c3aa82fecd27eaad5c0b2dcd80b`

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
| CodeQL | GREEN | Successful current execution-commit workflow |
| Snyk | GREEN | Successful current status |
| PwC evidence baseline | FROZEN | Baseline SHA retained without promotion |
| W3 schema/version authority | GREEN (bounded) | W3 evidence package + independent PostgreSQL re-performance |
| W3.1 logical PostgreSQL schema truth | GREEN (bounded) | W3.1-A closure evidence on exact execution commit `2d063f6b816a08899ee9f7f12cedf50322ea7099` |
| IAM / MFA organizational evidence (`GC-IDM-001/002`) | MISSING | Organizational MFA, privileged-access and review evidence not independently retained |
| Privileged access review | MISSING | Organizational access inventory/review records not independently retained |
| Main branch governance | VERIFIED (bounded) | Active repository ruleset `CORE-main-protection` provides PR, review, code-owner, thread-resolution and required-status-check controls |
| Post-merge main CI | PENDING | W3.1 evidence is on the feature-branch execution chain; final main evidence follows merge and revalidation |
| W3.1-B production DDL migration execution | OPEN / BLOCKED | W3.1-A does not authorize production migration execution; migration executor assurance remains separate |

## 3. Current technical state

W3.1-A technical closure is recorded in `docs/evidence/W3_1_CLOSURE_2026-09-17.md`. The exact execution commit is `2d063f6b816a08899ee9f7f12cedf50322ea7099`; evidence-lineage reconciliation is committed at `f7846aca4fb37c3aa82fecd27eaad5c0b2dcd80b`.

W3.1-A is bounded to the declared PostgreSQL logical-schema domain. It does not imply production migration execution, final CORE GREEN, or G86 LOCK.

## 4. Lock rule

Formal CORE LOCK is not declared until the remaining governance/evidence gaps are closed or explicitly accepted as audit exceptions by the responsible authority, the final audited commit is fixed, and the final assurance package is reconciled.

## 5. Non-negotiable audit principles

1. Source-code presence is not organizational control evidence.
2. A test PASS is not evidence that an organizational policy exists.
3. SHUUD is not included in CORE control conclusions.
4. Frozen PwC documents are not silently rewritten to claim later evidence.
5. Every final conclusion must identify the exact audited commit or retained evidence artifact.
6. Ambiguous states remain OPEN/MISSING rather than being promoted to PASS.
7. A PR head is not main-branch evidence until it is actually merged and the resulting main commit is revalidated.

## 6. Next closure sequence

1. Complete the protected review/merge path for PR #84.
2. Capture all required workflow evidence on the resulting main commit after merge.
3. Complete organizational IAM/MFA and privileged-access evidence.
4. Preserve and independently review the verified main-branch ruleset evidence.
5. Resolve or explicitly disposition the W3.1-B migration-executor boundary.
6. Produce final G1–G90 closure matrix and residual-unknown register.
7. Produce final immutable-SHA CORE LOCK record.
8. Only after CORE LOCK, resume SHUUD work.

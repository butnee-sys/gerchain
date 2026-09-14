# GerChain CORE — Final Closure Package

**Scope:** GerChain CORE only  
**Audit target commit:** `621e7e2acefe243d4c72e783970e1eb833c60b96`  
**Frozen PwC baseline:** `274f45c83ce088e2229a2628e3a80403a68503df`  
**SHUUD:** excluded from CORE assurance

## Purpose

This package defines the final evidence required to close the three remaining CORE audit controls. It is deliberately fail-closed: documentation, source code, or repository permissions alone do not constitute organizational assurance.

## 1. GC-IDM-001 — IAM/MFA evidence

**Current verdict: MISSING**

Required retained evidence:

1. Current GitHub organization/repository access inventory for privileged users.
2. MFA enforcement evidence for every privileged account with administrative access to the CORE repository or its governing organization.
3. Evidence date/time and organization scope.
4. Evidence that service accounts/bots with privileged capability are separately identified and governed.
5. Retention location and custodian for the evidence.

**Closure rule:** GC-IDM-001 becomes GREEN only after the responsible authority retains independently verifiable organizational IAM/MFA evidence tied to the audited environment.

**Do not use as substitute evidence:** application authorization tests, CODEOWNERS, branch rulesets, repository source code, or a statement that MFA is believed to be enabled.

## 2. GC-IDM-002 — Privileged access governance

**Current verdict: MISSING**

Required retained evidence:

1. Privileged-role inventory and role owner.
2. Evidence of approval/assignment of each privileged role.
3. Periodic privileged-access review or equivalent access recertification.
4. Joiner/mover/leaver or equivalent access-removal evidence.
5. Administrative access logging or equivalent traceability.
6. Evidence retention date and responsible custodian.

**Closure rule:** GC-IDM-002 becomes GREEN only when privileged access is demonstrably governed, reviewed, and traceable at the organizational level.

## 3. GC-IND-001 — Independent re-performance

**Current verdict: OPEN**

Required independent procedure:

1. Freeze the audit target commit: `621e7e2acefe243d4c72e783970e1eb833c60b96`.
2. Provide an independent reviewer with the repository, test instructions, and evidence index.
3. Reviewer independently reproduces the material CORE controls without relying on the developer's PASS conclusion.
4. Reviewer records environment, commands, timestamps, commit SHA, results, deviations, and conclusion.
5. Reviewer signs/dates the re-performance record and identifies their independence from implementation.
6. Retain raw test output and the signed conclusion with the audit evidence set.

**Minimum technical scope:** atomic release/idempotency, PostgreSQL concurrency, abandoned `PROCESSING` recovery, operating reconciliation, DEE security controls, CORE/SHUUD boundary, and relevant CI evidence.

**Closure rule:** GC-IND-001 becomes GREEN only after an independent reviewer has completed and retained the re-performance record.

## Final lock rule

All three controls must be GREEN, or formally accepted as audit exceptions by the responsible authority, before the CORE audit lock is declared.

Until then, GerChain CORE remains **technically verified but formally UNLOCKED**.

SHUUD work must not be promoted into the CORE assurance scope merely to close these controls.

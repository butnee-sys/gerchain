# GerChain — OpenSSF OSPS Baseline Assessment

**Assessment type:** Controlled working assessment
**Baseline version:** OSPS Baseline v2026.08.28
**Target level:** Level 1
**Repository:** butnee-sys/gerchain
**Assessment branch:** security/openssf-scorecard
**CORE technical baseline:** 621e7e2acefe243d4c72e783970e1eb833c60b96
**Status:** IN PROGRESS — no badge claim

## 1. Purpose

This document records a controlled assessment of GerChain CORE against the current Open Source Project Security (OSPS) Baseline Level 1. It is evidence preparation, not a certification, attestation, or independent audit opinion.

## 2. Assessment rule

Each criterion is classified conservatively as:

- MET — objective repository/platform evidence supports the requirement.
- PARTIAL — meaningful evidence exists but the requirement is not fully demonstrated.
- GAP — required evidence or implementation is not verified.
- N/A — applicability is formally justified.
- OPEN — requires additional verification.

A criterion is not marked MET merely because a similar technical feature exists elsewhere in the repository.

## 3. Initial verified observations

### Access control

- GitHub repository hosting provides the platform basis for MFA-protected access.
- Protected main-branch governance exists as repository ruleset evidence.
- Independent approval is required for protected changes.
- Current repository governance still has an open CODEOWNERS repair PR (#70), therefore related evidence remains OPEN until merged and verified on main.

### Security reporting

- SECURITY.md has been added on the assurance branch.
- It defines private vulnerability reporting, prohibited secret disclosure, triage/remediation expectations, and disclosure principles.
- It explicitly states that technical security assessments do not constitute ISO/IEC 27001 certification.

### Automated security assessment

- OpenSSF Scorecard workflow has been added on PR #71.
- Scorecard Action version 2.4.4 is used.
- SARIF output is uploaded to GitHub Code Scanning.
- A published Scorecard result has not yet been obtained on main; therefore Scorecard result evidence remains OPEN.

### Primary branch protection

- Main branch is protected against direct changes according to the existing repository ruleset evidence.
- Final Baseline-1 evidence remains OPEN until the current governance repair is merged and verified on main.

## 4. Known gaps requiring closure

1. Independent approval identity for protected changes.
2. CODEOWNERS presence on main branch.
3. OpenSSF Scorecard published result on main.
4. License information must be verified and, if required by Baseline criteria, added.
5. Project security/development documentation must be checked against all current Level-1 criteria.
6. Any remaining Baseline-1 automation or questionnaire results must be independently reviewed before marking MET.

## 5. Non-negotiable security rules

- No private keys, API tokens, passwords, production credentials, or other secrets are stored in this assessment document or repository.
- CORE runtime is not changed merely to manufacture compliance evidence.
- SHUUD remains outside CORE assurance scope.
- No OpenSSF badge is claimed until the external Best Practices Badge system reports the corresponding level as achieved.
- No ISO/IEC 27001 certification or conformity claim is made from this assessment.

## 6. Closure sequence

`PR #71 approval → merge → main Scorecard result → Baseline-1 questionnaire → resolve gaps → external badge verification → record evidence`

## 7. Source

The assessment uses the current OpenSSF OSPS Baseline v2026.08.28 as the governing external checklist. The baseline defines Level 1 as applicable to any code or non-code project and requires controls to be assessed against the stated MUST requirements.

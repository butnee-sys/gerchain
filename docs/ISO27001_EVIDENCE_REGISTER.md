# NEF–G-3–GerChain — ISO 27001 Evidence Register

**Document status:** Draft for controlled review  
**Version:** 0.1  
**ISMS scope:** NEF–G-3–GerChain core infrastructure  
**Technical baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`

## 1. Purpose

This register establishes the traceability layer between ISMS requirements, controls, risks and objective evidence. Evidence must be identifiable, reproducible, protected from unauthorized alteration and tied to a defined review point.

## 2. Evidence status

- **AVAILABLE:** evidence is identified and accessible for review.
- **PARTIAL:** evidence exists but does not fully satisfy the organizational requirement.
- **MISSING:** required evidence has not yet been produced or verified.
- **EXTERNAL:** evidence must come from an organization, supplier or independent assessor outside the repository.
- **OPEN:** applicability or ownership still requires confirmation.

## 3. Core evidence register

| Evidence ID | Control / area | Evidence | Source / location | Baseline / reference | Status | Verification owner |
|---|---|---|---|---|---|---|
| EV-001 | CORE baseline | Audited technical baseline | Git repository | `621e7e2...` | AVAILABLE | To assign |
| EV-002 | Change management | Protected main branch/ruleset | GitHub repository governance | `CORE-main-protection` | AVAILABLE | To assign |
| EV-003 | CI security | Required core-gates checks | GitHub Actions | main CI | AVAILABLE | To assign |
| EV-004 | Code security | CodeQL results | GitHub Actions | main CI | AVAILABLE | To assign |
| EV-005 | PostgreSQL integrity | Concurrency validation | GitHub Actions/tests | CORE PostgreSQL gate | AVAILABLE | To assign |
| EV-006 | Release integrity | Atomic release/idempotency tests | Repository tests | CORE test evidence | AVAILABLE | To assign |
| EV-007 | Recovery | GC-RES-003 abandoned PROCESSING recovery | Repository/CI evidence | PR #63 / merged evidence | AVAILABLE | To assign |
| EV-008 | Reconciliation | Operating reconciliation | Repository/CI evidence | PR #64 / core reconciliation | AVAILABLE | To assign |
| EV-009 | Witness integrity | Witness/tamper evidence controls | CORE evidence package | Control matrix | AVAILABLE | To assign |
| EV-010 | Cryptography | Cryptographic/decision controls | CORE evidence package | Control matrix | AVAILABLE | To assign |
| EV-011 | Scope boundary | CORE/SHUUD separation | Audit evidence package | Scope documents | AVAILABLE | To assign |
| EV-012 | Asset management | Information asset register | `ISO27001_INFORMATION_ASSET_REGISTER.md` | Current branch | PARTIAL | To assign |
| EV-013 | Classification | Information classification model | `ISO27001_INFORMATION_CLASSIFICATION.md` | Current branch | PARTIAL | To assign |
| EV-014 | Risk assessment | Risk register | `ISO27001_RISK_ASSESSMENT.md` | Current branch | PARTIAL | To assign |
| EV-015 | Risk treatment | Treatment plan | `ISO27001_RISK_TREATMENT_PLAN.md` | Current branch | PARTIAL | To assign |
| EV-016 | SoA | Statement of Applicability | `ISO27001_STATEMENT_OF_APPLICABILITY.md` | Current branch | PARTIAL | To assign |
| EV-017 | Control implementation | Control matrix | `ISO27001_CONTROL_MATRIX.md` | Current branch | PARTIAL | To assign |
| EV-018 | IAM/MFA | Organization identity and MFA evidence | Organizational system | External/controlled | MISSING | To assign |
| EV-019 | Privileged access | Privileged account register and review | Organizational system | External/controlled | MISSING | To assign |
| EV-020 | Key management | Key register/custody/lifecycle | Controlled security system | External/controlled | MISSING | To assign |
| EV-021 | Backup | Backup inventory and retention evidence | Operational infrastructure | External/controlled | MISSING | To assign |
| EV-022 | Restore | Successful restore test | Operational infrastructure | External/controlled | MISSING | To assign |
| EV-023 | Incident response | Approved procedure + exercise record | ISMS repository | External/controlled | MISSING | To assign |
| EV-024 | Supplier security | Supplier register/assessment/contracts | Contract repository | External/controlled | MISSING | To assign |
| EV-025 | Physical security | Facility/infrastructure assessment | Physical site evidence | External | MISSING | To assign |
| EV-026 | Legal compliance | Requirements register | Legal/compliance repository | External/controlled | MISSING | To assign |
| EV-027 | Personnel security | Screening/terms/NDA/training/offboarding evidence | HR/contract records | External/controlled | MISSING | To assign |
| EV-028 | Internal audit | Completed internal audit report | ISMS repository | Future | MISSING | To assign |
| EV-029 | Management review | Management review minutes/decisions | ISMS governance | Future | MISSING | To assign |
| EV-030 | Corrective action | Corrective-action register and closure evidence | ISMS repository | Future | MISSING | To assign |
| EV-031 | Independent assurance | Independent re-performance report | Independent assessor | GC-IND-001 | MISSING | Independent party |

## 4. Evidence integrity rules

Each evidence item should record, where applicable:

- evidence ID;
- description;
- source;
- creation date;
- review date;
- responsible owner;
- relevant control/risk;
- exact version, commit, run or record identifier;
- integrity mechanism where appropriate;
- retention period;
- access classification.

## 5. Technical evidence rule

A passing test is evidence of the behavior covered by that test. It is not, by itself, evidence of an organizational policy, role assignment, management review, personnel process or independent assurance.

## 6. Evidence preservation

Evidence linked to the frozen CORE baseline shall not be silently rewritten. If evidence is superseded, the new record shall identify the prior record and explain the change.

## 7. Evidence collection sequence

`Identify → Capture → Verify → Classify → Store → Link → Review → Preserve`

## 8. Immediate closure priorities

The first missing evidence to obtain should be:

1. organizational IAM/MFA;
2. privileged access;
3. cryptographic key management;
4. backup and restore testing;
5. incident response;
6. supplier security;
7. physical security;
8. legal/regulatory requirements;
9. personnel security;
10. independent re-performance.

## 9. Gate

**G6 — Evidence Register: OPEN.**

The register is structurally complete enough to drive evidence collection, but final GREEN requires actual evidence, named owners and verification records.

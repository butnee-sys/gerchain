# NEF–G-3–GerChain — Information Security Risk Assessment

**Document status:** Draft for controlled review  
**Version:** 0.1  
**ISMS scope:** NEF–G-3–GerChain core infrastructure  
**Technical baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`

## 1. Purpose

This register establishes the first controlled risk assessment for the proposed ISMS. It uses an organization-specific 1–5 likelihood and 1–5 impact scale. It is a working assessment and shall be validated by the responsible organization before risk acceptance or certification assessment.

## 2. Risk scoring

**Likelihood (L)**

1 — Rare  
2 — Unlikely  
3 — Possible  
4 — Likely  
5 — Almost certain

**Impact (I)**

1 — Negligible  
2 — Minor  
3 — Moderate  
4 — Major  
5 — Severe

**Risk score = L × I**

| Score | Level | Treatment expectation |
|---:|---|---|
| 1–4 | Low | Monitor / accept when justified |
| 5–9 | Medium | Treatment normally required |
| 10–16 | High | Priority treatment and management attention |
| 17–25 | Critical | Immediate treatment; acceptance only by formally authorized management |

## 3. Initial risk register

| ID | Asset / process | Threat / event | Vulnerability / condition | L | I | Initial risk | Existing technical controls | Residual assessment | Status |
|---|---|---|---|---:|---:|---:|---|---|---|
| R-001 | CORE source code | Unauthorized disclosure | Privileged repository access | 3 | 5 | 15 High | Protected main, PR governance, controlled repository | Medium–High pending IAM/MFA evidence | OPEN |
| R-002 | Cryptographic keys | Key theft or misuse | Key lifecycle/organizational evidence incomplete | 3 | 5 | 15 High | Cryptographic controls in CORE | High pending key-management evidence | OPEN |
| R-003 | Production credentials | Credential compromise | Privileged access governance incomplete | 3 | 5 | 15 High | Repository governance; secrets must be externalized | High | OPEN |
| R-004 | PostgreSQL data | Unauthorized alteration | Excessive or weakly governed database access | 3 | 5 | 15 High | Transaction integrity, concurrency tests, reconciliation | Medium–High | OPEN |
| R-005 | PostgreSQL data | Data loss / corruption | Recovery procedures not fully evidenced organizationally | 3 | 5 | 15 High | Transaction controls and recovery mechanisms | Medium–High | OPEN |
| R-006 | Escrow records | Unauthorized release | Authorization/control failure | 2 | 5 | 10 High | Atomic release, idempotency, witness controls | Medium | OPEN |
| R-007 | Escrow records | Duplicate processing | Replay/idempotency failure | 2 | 5 | 10 High | Idempotency controls and tests | Low–Medium | OPEN |
| R-008 | PROCESSING records | Abandoned operation | Worker/process failure | 2 | 4 | 8 Medium | GC-RES-003 recovery and reconciliation | Low–Medium | OPEN |
| R-009 | Witness Chain | Evidence tampering | Unauthorized modification or incomplete verification | 2 | 5 | 10 High | Integrity/tamper evidence controls | Low–Medium | OPEN |
| R-010 | Audit/reconciliation | Undetected inconsistency | Missing or delayed reconciliation | 2 | 5 | 10 High | Operating reconciliation and CORE evidence | Low–Medium | OPEN |
| R-011 | GitHub/CI | Unauthorized code change | Account compromise / weak privileged access | 3 | 5 | 15 High | Branch protection, PR review, required checks, CodeQL | High pending IAM/MFA | OPEN |
| R-012 | CI/CD | Malicious build/change | Pipeline compromise | 2 | 5 | 10 High | Required checks and protected main | Medium pending pipeline hardening evidence | OPEN |
| R-013 | Backup | Backup compromise | Inadequate access/retention evidence | 3 | 4 | 12 High | Technical recovery capability | High pending backup governance | OPEN |
| R-014 | Backup | Failed recovery | Recovery not periodically tested | 3 | 5 | 15 High | Recovery mechanisms | High pending tested restore evidence | OPEN |
| R-015 | Incident response | Delayed response | Formal procedure/register not completed | 3 | 4 | 12 High | Technical audit evidence | High | OPEN |
| R-016 | Personnel access | Insider misuse | IAM/MFA and privileged governance evidence missing | 3 | 5 | 15 High | Least-privilege principles in architecture | High | OPEN |
| R-017 | Supplier/service dependency | Third-party compromise/outage | Supplier security assessment incomplete | 3 | 4 | 12 High | Controlled architecture boundaries | High | OPEN |
| R-018 | Intellectual property | IP leakage or ownership dispute | Ownership chain and license register incomplete | 2 | 5 | 10 High | Git history and documentation | Medium–High | OPEN |
| R-019 | Security documentation | Incorrect or stale evidence | Version drift | 3 | 4 | 12 High | Git version history | Medium | OPEN |
| R-020 | Physical infrastructure | Unauthorized physical access | Physical security assessment incomplete | 3 | 4 | 12 High | Not yet formally assessed | High | OPEN |
| R-021 | Availability | Infrastructure outage | Dependency or capacity failure | 3 | 4 | 12 High | Recovery/transaction controls | Medium–High | OPEN |
| R-022 | Legal/regulatory | Non-compliance | Requirements register incomplete | 3 | 5 | 15 High | Governance documentation in progress | High | OPEN |
| R-023 | Independent assurance | False assurance claim | Technical PASS confused with organizational assurance | 2 | 5 | 10 High | Explicit evidence-package limitations | Low–Medium | OPEN |
| R-024 | Scope boundary | Uncontrolled scope expansion | SHUUD or other applications mixed into CORE assurance | 2 | 4 | 8 Medium | Explicit CORE/SHUUD boundary | Low | OPEN |

## 4. Highest-priority risks

The initial priority set is:

1. privileged identity and MFA assurance;
2. cryptographic key management;
3. production credentials;
4. backup and tested recovery;
5. incident response;
6. supplier security;
7. physical security;
8. legal/regulatory requirements;
9. IP ownership and licensing evidence;
10. independent re-performance.

These priorities reflect the current evidence gaps and do not mean the underlying technical controls are absent.

## 5. Existing CORE evidence that reduces technical risk

The assessment recognizes the following existing technical evidence:

- atomic release and idempotency controls;
- PostgreSQL concurrency validation;
- abandoned PROCESSING recovery;
- operating database reconciliation;
- Witness integrity controls;
- cryptographic/decision controls;
- protected main branch and pull-request governance;
- required CI checks;
- CodeQL security analysis;
- explicit CORE/SHUUD assurance boundary.

Technical evidence does not substitute for organizational ISMS evidence.

## 6. Risk acceptance rule

No HIGH or CRITICAL risk shall be marked accepted merely because a technical test passes. Formal acceptance requires:

- identified owner;
- documented treatment decision;
- target date;
- residual risk assessment;
- authorized management acceptance where applicable.

## 7. Risk treatment linkage

Each risk shall link to one or more of:

- existing control;
- new control;
- policy/procedure;
- technical change;
- organizational action;
- contractual action;
- monitoring activity;
- risk acceptance.

## 8. Gate

**G3 — Risk Assessment: OPEN.**

This register is not yet a final organizational risk acceptance record. Final GREEN requires management validation, named risk owners, treatment decisions and residual-risk acceptance where applicable.

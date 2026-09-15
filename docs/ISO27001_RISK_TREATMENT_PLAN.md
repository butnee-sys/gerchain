# NEF–G-3–GerChain — Risk Treatment Plan

**Document status:** Draft for controlled review  
**Version:** 0.1  
**ISMS scope:** NEF–G-3–GerChain core infrastructure

## 1. Purpose

This plan converts the initial risk assessment into controlled treatment actions. It deliberately separates technical remediation from organizational evidence so that the frozen GerChain CORE implementation is not changed merely to create ISO 27001 documentation.

## 2. Treatment options

- **Mitigate:** reduce likelihood or impact through controls.
- **Avoid:** stop or redesign the risky activity.
- **Transfer/share:** contractually or commercially transfer part of the risk.
- **Accept:** formally accept residual risk when justified.

## 3. Priority treatment plan

| Treatment ID | Risk IDs | Action | Type | Priority | Evidence required | Status |
|---|---|---|---|---|---|---|
| T-001 | R-001, R-011, R-016 | Establish organizational IAM, MFA and access-review policy | Organizational | Critical | IAM policy, MFA evidence, access review | OPEN |
| T-002 | R-002 | Establish cryptographic key lifecycle and custody procedure | Organizational + technical | Critical | Key register, custody procedure, review evidence | OPEN |
| T-003 | R-003 | Establish privileged-access management and credential handling | Organizational + technical | Critical | PAM/access policy, privileged account register | OPEN |
| T-004 | R-013, R-014 | Establish backup retention, protection and tested restore process | Operational | High | Backup register, restore test, evidence | OPEN |
| T-005 | R-015 | Establish incident response procedure and incident register | Organizational | High | Approved procedure, exercise/test evidence | OPEN |
| T-006 | R-017 | Establish supplier security assessment and contractual requirements | Organizational | High | Supplier register, assessments, contracts | OPEN |
| T-007 | R-020 | Complete physical security assessment for scoped infrastructure | Physical | High | Physical security assessment/evidence | OPEN |
| T-008 | R-022 | Establish information-security legal/regulatory requirements register | Compliance | High | Requirements matrix and review record | OPEN |
| T-009 | R-018 | Complete IP ownership chain and third-party license register | Legal/IP | High | Ownership records, license register | OPEN |
| T-010 | R-023 | Complete independent technical re-performance | Assurance | High | Independent report and evidence trail | OPEN |
| T-011 | R-019 | Establish controlled-document review and version process | Governance | Medium | Document register, review records | OPEN |
| T-012 | R-021 | Establish availability/continuity requirements and tests | Continuity | High | BCP/DR requirements and exercise evidence | OPEN |
| T-013 | R-024 | Maintain explicit CORE assurance boundary and change-control trigger | Governance | Medium | Scope review and change record | OPEN |

## 4. Treatment sequencing

### Phase A — Identity and privileged access

Complete T-001 and T-003 first because compromised privileged access can undermine multiple other controls.

### Phase B — Cryptography and recovery

Complete T-002 and T-004, including key custody and restore testing.

### Phase C — Operational resilience

Complete T-005 and T-012.

### Phase D — Third parties, physical and compliance

Complete T-006, T-007 and T-008.

### Phase E — IP and independent assurance

Complete T-009 and T-010.

### Phase F — Governance closure

Complete T-011 and T-013, then perform a full risk reassessment.

## 5. Treatment acceptance criteria

A treatment item is not GREEN merely because a document exists. Evidence shall demonstrate implementation and, where appropriate, operation and review.

Examples:

- IAM policy → actual account/MFA evidence → access review;
- backup procedure → actual backup → restore test;
- incident procedure → exercise or actual incident evidence;
- supplier policy → supplier assessment and contractual evidence;
- key procedure → controlled key register/custody evidence;
- independent assurance → independent re-performance result.

## 6. Residual risk

After treatment, each risk shall be rescored. Residual risk shall be compared with the organization's formally defined risk acceptance criteria.

## 7. Non-negotiable rule

The GerChain CORE technical baseline remains frozen unless a genuine security or reliability risk requires an implementation change. ISO 27001 documentation shall not be used as a reason to alter validated CORE behavior without a separate engineering change decision.

## 8. Gate

**G3 — Risk Treatment Plan: OPEN.**

GREEN requires named owners, target dates, implementation evidence and formal residual-risk decisions.

# NEF–G-3–GerChain — Internal ISMS Audit Plan

**Document status:** Draft for controlled review  
**Version:** 0.1  
**ISMS scope:** NEF–G-3–GerChain core infrastructure

## 1. Purpose

This plan defines the internal audit needed before any independent ISO 27001 assessment. The audit shall test whether the ISMS is established, implemented and maintained within its approved scope and whether evidence supports the stated control decisions.

## 2. Independence

The person performing the audit shall be sufficiently independent of the activity being audited. A person shall not approve their own control as an independent audit conclusion.

Where internal independence cannot reasonably be achieved, an external qualified reviewer shall be used.

## 3. Audit scope

The audit shall cover:

- approved ISMS scope;
- information asset register;
- classification and handling;
- risk assessment;
- risk treatment;
- Statement of Applicability;
- control implementation;
- evidence register;
- IAM/MFA;
- privileged access;
- cryptographic key management;
- backup/recovery;
- incident management;
- supplier security;
- physical security;
- legal/regulatory requirements;
- personnel security;
- change management;
- technical CORE evidence;
- document control;
- corrective action;
- management review readiness.

SHUUD application behavior remains outside the current CORE assurance scope unless the ISMS scope is formally expanded.

## 4. Audit method

For each sampled requirement/control:

`Requirement → Risk → Control → Evidence → Interview/Observation → Test → Finding → Corrective Action`

Audit evidence shall distinguish:

- conforming;
- partially conforming;
- nonconforming;
- observation/improvement opportunity;
- not applicable with documented justification.

## 5. Priority sampling

The first audit sample should include:

1. privileged account and MFA evidence;
2. repository branch protection and review;
3. a CORE release evidence chain;
4. PostgreSQL concurrency evidence;
5. reconciliation evidence;
6. key-management evidence;
7. backup and restore evidence;
8. incident-response exercise;
9. supplier assessment;
10. physical-security evidence;
11. one complete risk-treatment trace;
12. one complete evidence chain from control to underlying technical artifact.

## 6. Findings and corrective action

Every nonconformity shall have:

- finding ID;
- requirement/reference;
- objective evidence;
- root-cause analysis;
- correction;
- corrective action;
- responsible owner;
- target date;
- effectiveness verification;
- closure decision.

## 7. Audit output

The internal audit package shall contain:

- approved audit plan;
- audit criteria and scope;
- working papers/evidence references;
- findings;
- corrective-action register;
- final audit report;
- management response.

## 8. Gate

**G7 — Internal Audit: NOT STARTED.**

The audit shall not be represented as completed until the audit plan is executed and a dated report exists.

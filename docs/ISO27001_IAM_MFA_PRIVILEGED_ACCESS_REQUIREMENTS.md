# NEF–G-3–GerChain — IAM, MFA and Privileged Access Evidence Requirements

**Status:** Controlled evidence requirements — implementation pending  
**ISMS scope:** NEF–G-3–GerChain core infrastructure

## 1. Purpose

This document defines the minimum organizational evidence required to close the current ISO 27001 gaps for identity, authentication and privileged access. It does not claim that these controls are already implemented.

## 2. Required identity evidence

The organization shall establish and retain, as applicable:

- authoritative user/account register;
- role and responsibility mapping;
- account lifecycle procedure;
- joiner/mover/leaver records;
- unique account ownership;
- periodic access review;
- inactive-account handling;
- service-account inventory;
- emergency/break-glass account procedure.

## 3. MFA evidence

The organization shall document:

- systems requiring MFA;
- privileged accounts requiring MFA;
- MFA enrollment status;
- approved authentication methods;
- exception register and approval;
- periodic verification;
- recovery/reset controls.

Screenshots alone are not sufficient as the complete organizational control. They should be linked to the approved procedure, account inventory and review record.

## 4. Privileged access evidence

The organization shall establish:

- privileged-account register;
- named owner for each privileged account;
- business/technical justification;
- least-privilege role definition;
- approval record;
- access review frequency;
- privileged-session/logging evidence where applicable;
- removal/expiry process;
- emergency elevation process;
- segregation of duties where required.

## 5. GitHub repository governance

Repository controls are technical evidence only. The evidence package should connect:

`authorized person → organizational role → GitHub identity → repository permission → approval authority → review record`

The current protected-main ruleset is evidence of technical enforcement, not proof of the complete organizational IAM process.

## 6. Evidence owners

The following owners must be formally assigned before closure:

| Evidence area | Required owner | Status |
|---|---|---|
| ISMS ownership | Management-designated ISMS owner | OPEN |
| User/account register | Authorized administrator | OPEN |
| MFA register | Authorized administrator/security owner | OPEN |
| Privileged access | Security/technical owner | OPEN |
| Access review | Control owner | OPEN |
| GitHub governance | Repository administrator | OPEN |
| Evidence verification | Internal auditor/reviewer | OPEN |

## 7. Closure test

IAM/MFA/privileged-access status may move from MISSING to IMPLEMENTED/PARTIALLY IMPLEMENTED only after the organization provides objective evidence and a reviewer verifies it against the approved control requirements.

## 8. Security handling

This document must not contain passwords, private keys, recovery codes, API tokens or other authentication secrets. Such information belongs only in the approved secure secret-management mechanism.

## 9. Gate

**IAM/MFA/Privileged Access: MISSING — evidence collection required.**

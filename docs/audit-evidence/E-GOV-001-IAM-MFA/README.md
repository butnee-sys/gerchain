# E-GOV-001 — IAM/MFA Evidence Register

**Status:** OPEN — EVIDENCE NOT PROVIDED  
**Branch:** `audit/e-gov-001-iam-mfa-evidence`  
**Purpose:** Track evidence for identity and access management (IAM), privileged access, and multi-factor authentication (MFA). This register does not itself prove that controls are implemented.

## Current repository evidence

The branch was pushed, but the exported evidence directory was empty at the time of inspection. No control exports, configuration snapshots, access-review records, or MFA enforcement reports were present. Therefore, no IAM/MFA control is marked PASS.

## Required evidence

| ID | Control | Required evidence | Acceptance condition | Status |
|---|---|---|---|---|
| E-GOV-001-A | Identity source and account inventory | Dated export of users, service accounts, privileged accounts, and identity provider/source | Complete scope, owner, export timestamp, and reproducible source | MISSING |
| E-GOV-001-B | MFA enforcement | IdP/security-policy export and report of MFA enrollment/enforcement for privileged users | Enforcement is mandatory for all privileged human accounts; exceptions are documented and approved | MISSING |
| E-GOV-001-C | Privileged access | Role/group membership export and privilege assignment rationale | Least privilege, named owners, and no unexplained privileged access | MISSING |
| E-GOV-001-D | Access review | Signed or attributable review of active/privileged accounts | Review date, reviewer, decisions, removals, and unresolved exceptions recorded | MISSING |
| E-GOV-001-E | Service and recovery accounts | Inventory of service accounts, tokens, break-glass accounts, and recovery methods | Owners, purpose, restrictions, rotation/recovery controls, and monitoring documented | MISSING |
| E-GOV-001-F | Auditability | Authentication/MFA and privileged-action logs covering a defined period | Source, time window, retention, integrity, and review evidence documented | MISSING |
| E-GOV-001-G | Independent verification | Re-performance record against the exported evidence | Reviewer can reproduce the result without relying on an unsupported assertion | MISSING |

## Evidence handling

For every export, preserve:
- originating system and exact query/report name;
- export timestamp and covered period;
- operator/reviewer identity and role;
- original file checksum (SHA-256);
- any redactions, with rationale;
- the control ID(s) supported by the file.

Do not commit passwords, MFA seeds, recovery codes, private keys, session tokens, raw secrets, or unnecessary personal data. Redact secrets before export. Keep the unredacted source only in the approved restricted evidence store.

## Decision rule

A control is PASS only when its required evidence exists, is in scope, is current, and has been independently checked. Missing or ambiguous evidence remains **MISSING / UNVERIFIED**; it must not be treated as a pass.

**Current conclusion:** E-GOV-001 IAM/MFA remains **OPEN**. Creating this register is documentation progress, not evidence that IAM or MFA controls are operating.

# GerChain CORE — Final Audit Evidence Checklist

**Audited technical baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`

**Purpose:** retain a fail-closed checklist for the three remaining audit closure items without manufacturing evidence.

## 1. GC-IDM-001 — IAM / MFA

**Status:** MISSING

### Required evidence
- Current privileged-account inventory for the repository / production administration boundary.
- MFA enforcement evidence for every privileged account in scope.
- Evidence date, system owner, and scope of the evidence.
- Evidence retained in an auditable location and linked to the audited baseline.

### Acceptance rule
PASS only when an authorized reviewer can independently verify that privileged accounts are identified and MFA is enforced for the in-scope accounts.

Repository source code, CODEOWNERS, cryptographic controls, or successful CI tests do **not** prove organizational MFA.

## 2. GC-IDM-002 — Privileged Access Governance

**Status:** MISSING

### Required evidence
- Privileged-role assignment inventory.
- Approval / authorization record for privileged access.
- Periodic access review evidence.
- Joiner / mover / leaver or equivalent access lifecycle evidence.
- Administrative access logging or equivalent accountability evidence.
- Evidence owner and review date.

### Acceptance rule
PASS only when privileged access is demonstrably authorized, reviewed, attributable, and removable.

Application-level authorization tests do **not** substitute for organizational privileged-access governance evidence.

## 3. GC-IND-001 — Independent Re-performance

**Status:** OPEN

### Required evidence
An independent reviewer, not the person responsible for implementing the controls, should re-perform the agreed CORE control set against the immutable technical baseline `621e7e2acefe243d4c72e783970e1eb833c60b96`.

The evidence package should contain:
- reviewer identity / organization;
- date and environment;
- exact commit SHA tested;
- commands / procedures performed;
- observed results;
- deviations or exceptions;
- reviewer conclusion;
- signed or otherwise attributable review record.

### Acceptance rule
PASS only after independent re-performance is actually completed and attributable evidence is retained.

## Fail-closed final rule

No remaining item may be changed to GREEN solely because a document, source-code control, or internal test exists.

The final CORE audit state is therefore:

- Technical CORE: GREEN where independently reproducible repository evidence exists.
- Main governance / CI: GREEN where verified against the audited baseline.
- GC-IDM-001: MISSING until organizational IAM/MFA evidence exists.
- GC-IDM-002: MISSING until privileged-access governance evidence exists.
- GC-IND-001: OPEN until independent re-performance is completed.

SHUUD is outside this closure package unless the formal audit scope is explicitly expanded.

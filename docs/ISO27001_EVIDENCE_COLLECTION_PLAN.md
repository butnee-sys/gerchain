# NEF–G-3–GerChain — ISO/IEC 27001 Evidence Collection Plan

**Status:** Controlled execution plan
**Branch:** `docs/iso27001-alignment`
**Technical CORE baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`

## 1. Objective

Convert the existing ISO documentation structure into an executable evidence-collection programme without modifying GerChain CORE merely to manufacture compliance evidence.

## 2. Collection sequence

| Wave | Evidence | Required output | Current state |
|---|---|---|---|
| W1 | IAM/MFA | identity register, MFA evidence, review | MISSING |
| W2 | Privileged access | privileged account register, approvals, review | MISSING |
| W3 | Key management | key register, custody, rotation/revocation evidence | MISSING |
| W4 | Backup/restore | backup register + successful restore record | MISSING |
| W5 | Incident response | approved procedure + exercise/incident record | MISSING |
| W6 | Supplier security | supplier register + assessment/contract evidence | MISSING |
| W7 | Physical security | site/facility assessment | MISSING |
| W8 | Legal/regulatory | applicability register + review | MISSING |
| W9 | Personnel security | role/NDA/training/offboarding evidence | MISSING |
| W10 | Independent assurance | re-performance report | PENDING |

## 3. Evidence acceptance test

Each item becomes **AVAILABLE** only when:

1. source is identified;
2. responsible owner is named;
3. evidence is dated/versioned;
4. evidence can be independently reviewed;
5. classification/access restrictions are defined;
6. the linked control/risk is explicit;
7. reviewer records a decision.

## 4. Organizational evidence rule

Repository documentation defines requirements and traceability. It does not substitute for actual organizational records such as account reviews, approvals, training records, contracts, facility assessments or management decisions.

## 5. Technical evidence preservation

Existing CORE evidence shall remain linked to its exact baseline/run/PR where applicable. The frozen CORE technical baseline shall not be silently rewritten during ISO evidence collection.

## 6. Completion rule

When W1–W9 have objective evidence, update the Evidence Register and Control Matrix. Then execute G7 internal audit. After corrective actions and management review, proceed to G9 independent assessment.

## 7. Final state

**Current collection programme: ACTIVE.**
**Certification claim: NOT AUTHORIZED.**

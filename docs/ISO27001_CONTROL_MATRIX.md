# NEF–G-3–GerChain — ISO 27001 Control Implementation Matrix

**Document status:** Draft for controlled review  
**Version:** 0.1  
**ISMS scope:** NEF–G-3–GerChain core infrastructure

## 1. Purpose

This matrix links the SoA decisions to implementation evidence, ownership and remaining work. It is intentionally an evidence-oriented management document rather than a copy of the ISO standard.

## 2. Status definitions

- **GREEN:** implementation and evidence are sufficient for the current review stage.
- **YELLOW:** implementation exists partially, or evidence is incomplete.
- **RED:** required implementation/evidence is missing.
- **OPEN:** decision requires organizational confirmation.

## 3. Priority control matrix

| ID | Control domain | Current implementation | Evidence source | Status | Required closure |
|---|---|---|---|---|---|
| CM-001 | Security policy | ISMS documentation being established | ISO27001 workplan | YELLOW | Management approval |
| CM-002 | Asset management | Asset register established | ISO27001 asset register | YELLOW | Owners/classification confirmation |
| CM-003 | Information classification | Four-level model established | Classification document | YELLOW | Formal approval and deployment |
| CM-004 | Access governance | Technical repository controls exist | Main branch/ruleset evidence | YELLOW | Organization-wide IAM/MFA evidence |
| CM-005 | Privileged access | Technical boundary identified | Risk register | RED | Privileged account register + MFA + review |
| CM-006 | Identity lifecycle | Not yet formally evidenced | Risk register | RED | Joiner/mover/leaver process |
| CM-007 | Supplier security | Not formally established | Risk treatment plan | RED | Supplier register and assessments |
| CM-008 | Incident management | Technical evidence exists; formal process incomplete | Audit/evidence package | YELLOW | Incident procedure + exercise |
| CM-009 | Business continuity | Recovery mechanisms exist | CORE recovery evidence | YELLOW | Formal BCP/DR and restore tests |
| CM-010 | Legal/regulatory compliance | Legal matrix not completed | Risk register | RED | Requirements register |
| CM-011 | IP protection | Git history and documentation exist | Repository/history | YELLOW | Ownership and license register |
| CM-012 | Independent review | Not completed | GC-IND-001 | RED | Independent re-performance |
| CM-013 | Physical security | Not assessed | Risk register | RED | Physical assessment |
| CM-014 | Secure development | PR/review/branch controls exist | CORE governance | GREEN/YELLOW | Formal SDL procedure |
| CM-015 | Source-code protection | Protected main + repository controls | CORE governance | GREEN/YELLOW | Full access review |
| CM-016 | Vulnerability management | CodeQL/security checks exist | CI evidence | YELLOW | Formal vulnerability process |
| CM-017 | Configuration/change management | Git and protected main | Ruleset/PR evidence | GREEN/YELLOW | Configuration baseline |
| CM-018 | Logging/auditability | Witness/audit/reconciliation controls | CORE evidence | GREEN/YELLOW | Retention/monitoring policy |
| CM-019 | Cryptography | Technical cryptographic controls | CORE evidence | GREEN/YELLOW | Key lifecycle/custody evidence |
| CM-020 | Database integrity | PostgreSQL transaction/concurrency evidence | CORE tests | GREEN | Operational evidence maintenance |
| CM-021 | Release integrity | Atomic release/idempotency/recovery evidence | CORE tests | GREEN | Periodic regression |
| CM-022 | Reconciliation | Operating reconciliation implemented | CORE evidence | GREEN | Periodic review |
| CM-023 | Security testing | Automated validation + CodeQL | CI/test evidence | GREEN/YELLOW | Broader security test programme |
| CM-024 | Documentation control | Git versioning exists | Repository history | YELLOW | Controlled document register/review |

## 4. Technical GREEN does not equal ISMS GREEN

A control may be technically GREEN while its organizational evidence remains incomplete. For example, PostgreSQL transaction integrity can be technically demonstrated without proving that the organization has completed its formal access-review, incident-management or management-review obligations.

Therefore the final certification-readiness decision must consider both technical and organizational evidence.

## 5. Evidence hierarchy

Evidence should be evaluated in this order:

1. approved policy/procedure;
2. assigned owner/responsibility;
3. implemented control;
4. operational record;
5. periodic review;
6. internal audit result;
7. corrective action where needed;
8. independent assessment where required.

## 6. Gate

**G5 — Control Implementation and Evidence: OPEN.**

The matrix establishes traceability but is not yet final evidence of organizational conformity.

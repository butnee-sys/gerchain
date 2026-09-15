# NEF–G-3–GerChain — ISO/IEC 27001:2023 Annex A GAP Closure Plan

**Document status:** Controlled working plan  
**Version:** 0.1  
**Branch:** `docs/iso27001-alignment`  
**Technical baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`  
**Scope:** NEF–G-3–GerChain core infrastructure; SHUUD excluded.

## 1. Purpose

This plan converts the 93-control Annex A assessment into an executable closure sequence. It does not change the frozen CORE merely to manufacture ISO evidence.

## 2. Closure principle

A GAP is closed only when objective evidence exists and is reviewed by an authorized owner. A repository document alone does not close an organizational control.

Promotion rule:

`GAP → PARTIAL → GREEN`

Required evidence chain:

`Source → Owner → Date/Version → Traceability → Review → Decision`

## 3. Work packages

| WP | Controls | Priority | Required closure evidence | Status |
|---|---|---|---|---|
| WP1 | A.5.1–A.5.6 | Critical | Approved policy, role matrix, management responsibility, authority/special-interest contact records | OPEN |
| WP2 | A.5.7–A.5.15 | High | Threat intelligence, project security, asset ownership, classification, acceptable use, transfer controls | OPEN |
| WP3 | A.5.16–A.5.18, A.8.2, A.8.5 | Critical | Identity register, MFA evidence, privileged account register, access review | OPEN |
| WP4 | A.5.19–A.5.23 | Critical | Supplier register, due diligence, security clauses, ICT supply-chain review, supplier monitoring, cloud responsibility model | OPEN |
| WP5 | A.5.24–A.5.30, A.8.13–A.8.16 | Critical | Incident procedure/exercise, evidence procedure, continuity plan, backup/restore test, logging retention, monitoring records | OPEN |
| WP6 | A.5.31–A.5.37 | High | Legal register, IP register, privacy assessment, independent review, internal audit, operating procedures | OPEN |
| WP7 | A.6.1–A.6.8 | High | Personnel contracts, NDA, training, screening where applicable, disciplinary/offboarding/reporting records | OPEN |
| WP8 | A.7.1–A.7.14 | High | Physical site assessment, entry/access, environmental protection, media, equipment, maintenance and disposal records | OPEN |
| WP9 | A.8.1, A.8.3–A.8.12, A.8.14, A.8.17–A.8.23 | High | Endpoint, vulnerability, configuration, deletion, DLP, redundancy, monitoring, time, network and software controls | OPEN |
| WP10 | A.8.24–A.8.34 | High | Key custody/lifecycle, SDL, requirements, architecture review, secure coding, security testing, environment separation, change/test/audit controls | PARTIAL→OPEN |

## 4. Immediate execution order

1. IAM/MFA and privileged access.
2. Cryptographic key custody and lifecycle.
3. Backup and restore evidence.
4. Incident response and exercise.
5. Supplier and ICT supply-chain controls.
6. Physical security assessment.
7. Legal/regulatory/IP/privacy applicability.
8. Personnel security.
9. Convert existing technical PARTIAL controls to objective operating evidence.
10. Run internal audit.
11. Close corrective actions and verify effectiveness.
12. Conduct management review.
13. Prepare independent assessment/re-performance.

## 5. Technical controls that must remain frozen

The following CORE assurance baseline is not to be altered merely for ISO documentation:

- transaction/release integrity;
- idempotency;
- PostgreSQL transaction/concurrency controls;
- abandoned PROCESSING recovery;
- reconciliation;
- Witness/audit evidence;
- cryptographic decision controls;
- protected main/review governance;
- required CORE CI gates.

Any genuine security defect discovered during GAP closure is handled as an engineering change through normal protected change management.

## 6. Closure evidence standard

Evidence must be:

- objective;
- attributable to an owner;
- dated/versioned;
- traceable to the control and risk;
- reviewable;
- appropriately classified;
- free of secrets/private keys/passwords/tokens;
- retained according to the approved evidence/records policy.

## 7. Exit criteria

The ISO readiness effort is not complete until:

- ISMS scope is approved;
- risk assessment and treatment are approved;
- SoA covers all applicable controls and includes justified exclusions where applicable;
- objective evidence is available;
- internal audit is completed;
- corrective actions are verified;
- management review is completed;
- independent assessment/re-performance is completed or formally scheduled as the next assurance step.

## 8. Claim restriction

Until the above exit criteria are met, no statement such as “ISO/IEC 27001 certified” or “fully conformant” is authorized.

Approved working wording:

> **NEF–G-3–GerChain үндсэн бүтцийн мэдээллийн аюулгүй байдлын менежментийн тогтолцоог MNS ISO/IEC 27001:2023-д нийцүүлэн бүрдүүлж, хэрэгжүүлэх шатанд байна.**

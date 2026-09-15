# MNS ISO/IEC 27001:2023 — Final Execution Tracker

**Status:** Controlled working tracker  
**Branch:** `docs/iso27001-alignment`  
**CORE technical baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`

## Purpose

This tracker is the single execution view for closing the ISMS readiness work. It does not itself constitute certification, conformity assessment or an audit opinion.

## Gate status

| Gate | Scope | Current state | Exit evidence |
|---|---|---|---|
| G1 | ISMS scope/context | OPEN | Approved scope, boundaries, interested parties |
| G2 | Information assets | PARTIAL | Named owners, classification, treatment |
| G3 | Risk and treatment | OPEN | Approved risk register, treatment and residual-risk decisions |
| G4 | Statement of Applicability | OPEN | 93/93 controls mapped, applicability and treatment approved |
| G5 | Control implementation | PARTIAL | Objective operating evidence for applicable controls |
| G6 | Evidence system | PARTIAL | Complete attributable, dated, traceable evidence |
| G7 | Internal audit | NOT STARTED | Independent internal audit report + findings |
| CA | Corrective action | NOT STARTED | Root cause, action, effectiveness verification |
| G8 | Management review | NOT PERFORMED | Dated management-review record and decisions |
| G9 | Independent assessment | PENDING | Independent re-performance/assessment result |

## Work package order

1. **WP1** — IAM/MFA and identity governance
2. **WP2** — Privileged access and segregation of duties
3. **WP3** — Cryptographic key lifecycle and custody
4. **WP4** — Supplier, ICT supply chain and cloud security
5. **WP5** — Backup, continuity, incident response, logging and monitoring
6. **WP6** — Governance, legal, regulatory, privacy, IP and records
7. **WP7** — Personnel security
8. **WP8** — Physical security
9. **WP9** — Technical PARTIAL controls → objective operating evidence
10. **G7** — Internal audit
11. **CA** — Corrective action and effectiveness verification
12. **G8** — Management review
13. **G9** — Independent assessment

## Non-negotiable controls

- CORE baseline remains frozen unless a genuine security/engineering defect requires a protected change.
- Documentation alone never becomes objective operating evidence.
- Source code/tests are not treated as proof of organization-wide policy operation.
- No secrets are stored in the repository.
- SHUUD remains outside CORE ISMS assurance scope unless the approved scope is explicitly expanded.
- No ISO certification or full-conformity claim before G9 closure.

## Evidence promotion rule

`Requirement → Source → Owner → Date/Version → Operation → Traceability → Review → Decision → Retention`

## Current conclusion

The NEF–G-3–GerChain ISMS alignment program is **IN PROGRESS**. The technical CORE foundation is substantially evidenced, while organizational, physical, personnel, operational and independent-assurance evidence remains to be closed.

Authorized wording:

> “NEF–G-3–GerChain үндсэн бүтцийн мэдээллийн аюулгүй байдлын менежментийн тогтолцоог MNS ISO/IEC 27001:2023-д нийцүүлэн бүрдүүлж, хэрэгжүүлэх шатанд байна.”

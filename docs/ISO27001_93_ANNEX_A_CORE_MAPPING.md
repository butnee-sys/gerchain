# NEF–G-3–GerChain — ISO/IEC 27001:2023 Annex A — 93 Control CORE Mapping

**Document status:** Controlled working assessment  
**Version:** 0.1  
**Branch:** `docs/iso27001-alignment`  
**Technical baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`  
**Scope:** NEF–G-3–GerChain core infrastructure; SHUUD application scope excluded.  

## 1. Assessment rule

This matrix compares the 93 Annex A controls against the current NEF–G-3–GerChain CORE architecture and available evidence. It does **not** claim certification or full conformity.

- **GREEN** — objective evidence supports the control objective within the defined technical/organizational boundary.
- **PARTIAL** — meaningful technical or process evidence exists, but organizational evidence, full coverage, or formal operation is incomplete.
- **GAP** — required implementation/evidence is not currently verified.

A source-code feature or automated test is not by itself evidence of an organization-wide ISMS control.

ISO guidance states that Annex A is used to compare against controls determined through risk treatment and to verify that necessary controls have not been omitted; it is not intended to be used as a simple comprehensive checklist. Therefore, final applicability decisions remain subject to the approved risk assessment and SoA. 

## 2. 93-control mapping

### A.5 Organizational controls — 37

| Ref | Control | CORE relationship | Status | Closure / evidence |
|---|---|---|---|---|
| A.5.1 | Information security policies | ISMS governance layer | GAP | Approved policy suite |
| A.5.2 | Information security roles and responsibilities | Governance/ownership | GAP | Named owners and responsibility matrix |
| A.5.3 | Segregation of duties | PR/review supports technical separation | PARTIAL | Formal role/conflict matrix |
| A.5.4 | Management responsibilities | Governance | GAP | Management approval and review evidence |
| A.5.5 | Contact with authorities | Legal/incident interface | GAP | Authority contact register/process |
| A.5.6 | Contact with special interest groups | Threat/security ecosystem | GAP | Relevant memberships/contact process |
| A.5.7 | Threat intelligence | Security monitoring | GAP | Threat-intelligence source and review record |
| A.5.8 | Information security in project management | PR/change governance | PARTIAL | Formal ISMS project-security procedure |
| A.5.9 | Inventory of information and other associated assets | Asset register | PARTIAL | Owner/classification verification |
| A.5.10 | Acceptable use of information and associated assets | Asset handling | GAP | Approved acceptable-use rules |
| A.5.11 | Return of assets | Personnel/offboarding | GAP | Return/termination records |
| A.5.12 | Classification of information | Classification framework | PARTIAL | Formal approval and operating records |
| A.5.13 | Labelling of information | Classification implementation | GAP | Labelling/handling procedure |
| A.5.14 | Information transfer | Data transfer | GAP | Transfer procedure and records |
| A.5.15 | Access control | Repository/role controls | PARTIAL | Organization-wide access policy/evidence |
| A.5.16 | Identity management | IAM | GAP | Identity lifecycle register |
| A.5.17 | Authentication information | Credentials/MFA | GAP | Credential and MFA evidence |
| A.5.18 | Access rights | Branch/repository controls | PARTIAL | Periodic access review records |
| A.5.19 | Information security in supplier relationships | Supplier governance | GAP | Supplier register/due diligence |
| A.5.20 | Addressing information security within supplier agreements | Contract controls | GAP | Security clauses/contracts |
| A.5.21 | Managing information security in the ICT supply chain | Supplier chain | GAP | ICT supply-chain assessment |
| A.5.22 | Monitoring, review and change management of supplier services | Supplier oversight | GAP | Supplier review/change records |
| A.5.23 | Information security for use of cloud services | Cloud boundary | GAP | Cloud inventory/shared-responsibility review |
| A.5.24 | Information security incident management planning and preparation | Incident framework | GAP | Approved incident plan |
| A.5.25 | Assessment and decision on information security events | Incident triage | GAP | Classification/triage procedure |
| A.5.26 | Response to information security incidents | Incident response | GAP | Procedure + operational exercise |
| A.5.27 | Learning from information security incidents | Corrective learning | GAP | Post-incident review records |
| A.5.28 | Collection of evidence | Witness/audit records | PARTIAL | Formal evidence procedure and chain-of-custody |
| A.5.29 | Information security during disruption | Recovery/continuity | PARTIAL | Formal continuity controls and tests |
| A.5.30 | ICT readiness for business continuity | Recovery mechanisms | PARTIAL | RPO/RTO + restore/continuity evidence |
| A.5.31 | Legal, statutory, regulatory and contractual requirements | Legal register | GAP | Applicability register and review |
| A.5.32 | Intellectual property rights | IP governance | GAP | IP ownership/licence register |
| A.5.33 | Protection of records | Audit/reconciliation records | PARTIAL | Retention/protection policy |
| A.5.34 | Privacy and protection of PII | Conditional data scope | GAP | PII inventory + legal assessment |
| A.5.35 | Independent review of information security | Independent assurance | GAP | Independent re-performance/review |
| A.5.36 | Compliance with policies, rules and standards for information security | Internal audit | GAP | Internal audit evidence |
| A.5.37 | Documented operating procedures | Technical procedures | PARTIAL | Approved operational procedures |

### A.6 People controls — 8

| Ref | Control | CORE relationship | Status | Closure / evidence |
|---|---|---|---|---|
| A.6.1 | Screening | Personnel security | GAP | Applicable screening records/process |
| A.6.2 | Terms and conditions of employment | Personnel security | GAP | Contractual security clauses |
| A.6.3 | Information security awareness, education and training | Human control | GAP | Training plan and attendance/evidence |
| A.6.4 | Disciplinary process | Governance | GAP | Approved disciplinary process |
| A.6.5 | Responsibilities after termination or change of employment | Access lifecycle | GAP | Offboarding/access-removal records |
| A.6.6 | Confidentiality or non-disclosure agreements | IP/source protection | GAP | NDA/contract evidence |
| A.6.7 | Remote working | Access boundary | GAP | Remote-work/security policy |
| A.6.8 | Information security event reporting | Incident input | GAP | Reporting channel and records |

### A.7 Physical controls — 14

| Ref | Control | CORE relationship | Status | Closure / evidence |
|---|---|---|---|---|
| A.7.1 | Physical security perimeters | Infrastructure boundary | GAP | Site inventory/assessment |
| A.7.2 | Physical entry | Facility access | GAP | Entry control evidence |
| A.7.3 | Securing offices, rooms and facilities | Facility security | GAP | Site assessment |
| A.7.4 | Physical security monitoring | Facility monitoring | GAP | Applicable monitoring evidence |
| A.7.5 | Protecting against physical and environmental threats | Resilience | GAP | Environmental risk assessment |
| A.7.6 | Working in secure areas | Secure-area procedure | GAP | Procedure and records |
| A.7.7 | Clear desk and clear screen | Information handling | GAP | Policy/evidence |
| A.7.8 | Equipment siting and protection | Infrastructure | GAP | Equipment/site assessment |
| A.7.9 | Security of assets off-premises | Asset handling | GAP | Off-premises asset process |
| A.7.10 | Storage media | Data/media protection | GAP | Media register/handling/disposal |
| A.7.11 | Supporting utilities | Availability | GAP | Utility dependency/continuity evidence |
| A.7.12 | Cabling security | Physical infrastructure | GAP | Applicability/site assessment |
| A.7.13 | Equipment maintenance | Infrastructure | GAP | Maintenance records |
| A.7.14 | Secure disposal or re-use of equipment | Asset lifecycle | GAP | Disposal/reuse records |

### A.8 Technological controls — 34

| Ref | Control | CORE relationship | Status | Closure / evidence |
|---|---|---|---|---|
| A.8.1 | User endpoint devices | Endpoint boundary | GAP | Endpoint inventory/security baseline |
| A.8.2 | Privileged access rights | Privileged access | GAP | Privileged account register/MFA/review |
| A.8.3 | Information access restriction | Repository/role controls | PARTIAL | Organization-wide access evidence |
| A.8.4 | Access to source code | Protected repository | PARTIAL | Repository governance + periodic review |
| A.8.5 | Secure authentication | Authentication | GAP | MFA/authentication evidence |
| A.8.6 | Capacity management | Runtime infrastructure | GAP | Capacity thresholds/monitoring |
| A.8.7 | Protection against malware | Endpoint/server security | GAP | Protection evidence |
| A.8.8 | Management of technical vulnerabilities | CodeQL/security checks | PARTIAL | Vulnerability register, remediation SLA and review |
| A.8.9 | Configuration management | Git/configuration governance | PARTIAL | Approved configuration baseline |
| A.8.10 | Information deletion | Data lifecycle | GAP | Deletion/retention process |
| A.8.11 | Data masking | Conditional | GAP | Data inventory and masking assessment |
| A.8.12 | Data leakage prevention | Data transfer boundary | GAP | DLP assessment/controls |
| A.8.13 | Information backup | Recovery | GAP | Actual backup/restore evidence |
| A.8.14 | Redundancy of information processing facilities | Availability | GAP | Redundancy architecture/evidence |
| A.8.15 | Logging | Audit/Witness records | PARTIAL | Retention, monitoring and access evidence |
| A.8.16 | Monitoring activities | Security monitoring | GAP | Monitoring process and records |
| A.8.17 | Clock synchronization | Infrastructure | GAP | Time synchronization evidence |
| A.8.18 | Use of privileged utility programs | Privileged tooling | GAP | Tool register and control |
| A.8.19 | Installation of software on operational systems | Change control | GAP | Approved software/change process |
| A.8.20 | Networks security | Network boundary | GAP | Network security baseline |
| A.8.21 | Security of network services | Service inventory | GAP | Network-service requirements |
| A.8.22 | Segregation of networks | Network architecture | GAP | Segmentation evidence |
| A.8.23 | Web filtering | Conditional endpoint scope | GAP | Applicability assessment |
| A.8.24 | Use of cryptography | Cryptographic controls | PARTIAL | Key lifecycle/custody evidence |
| A.8.25 | Secure development life cycle | PR/CI/test governance | PARTIAL | Formal SDL and records |
| A.8.26 | Application security requirements | CORE requirements/tests | PARTIAL | Formal security-requirements process |
| A.8.27 | Secure system architecture and engineering principles | CORE architecture | PARTIAL | Formal architecture/security review |
| A.8.28 | Secure coding | Review/CI/security scanning | PARTIAL | Secure-coding standard and evidence |
| A.8.29 | Security testing in development and acceptance | Automated CORE tests/CodeQL | PARTIAL | Broader security test programme |
| A.8.30 | Outsourced development | Supplier/contractor boundary | GAP | Outsourced-development assessment |
| A.8.31 | Separation of development, test and production environments | Environment governance | GAP | Environment inventory/segregation evidence |
| A.8.32 | Change management | Protected main/PR/checks | PARTIAL | Full organizational change procedure |
| A.8.33 | Test information | Test-data handling | GAP | Test-data classification/control |
| A.8.34 | Protection of information systems during audit testing | Audit testing | GAP | Authorized audit-test procedure |

## 3. Current result

**Total controls mapped: 93/93.**

Current working classification:

- **GREEN: 0** — no Annex A control is promoted to fully GREEN solely from the present repository evidence.
- **PARTIAL: 24** — meaningful CORE technical/process evidence exists but organization-wide ISMS evidence or complete operating coverage is not yet demonstrated.
- **GAP: 69** — required organizational, physical, procedural, or technical evidence/implementation is not currently verified.

This conservative result is intentional. It prevents a technical repository test from being mistaken for organization-wide conformity.

## 4. Highest-priority closure sequence

1. A.5.1–A.5.4 — policy, roles, management responsibility and segregation of duties.
2. A.5.16–A.5.18 + A.8.2 + A.8.5 — IAM, MFA and privileged access.
3. A.5.19–A.5.23 — supplier/cloud governance, including the four controls previously omitted from the draft SoA.
4. A.5.24–A.5.30 + A.8.13–A.8.16 — incident, continuity, backup, logging and monitoring.
5. A.5.31–A.5.36 — legal, IP, privacy, independent review and internal audit.
6. A.6 — personnel controls.
7. A.7 — physical controls.
8. A.8 remaining technological controls.
9. Internal audit → corrective action → management review → independent assessment.

## 5. Final interpretation

The current evidence supports a **strong technical CORE foundation**, especially around transaction integrity, release integrity, recovery, reconciliation, Witness/audit evidence, cryptographic decision controls, repository governance and automated security checks. However, the current repository does not constitute a complete ISO/IEC 27001 ISMS.

Therefore the correct public/official wording remains:

> **“NEF–G-3–GerChain үндсэн бүтцийн мэдээллийн аюулгүй байдлын менежментийн тогтолцоог MNS ISO/IEC 27001:2023-д нийцүүлэн бүрдүүлж, хэрэгжүүлэх шатанд байна.”**

Certification or full-conformity claims are not authorized until the ISMS requirements, objective evidence, internal audit, management review and independent/certification assessment are completed.

## 6. Important note

This document is an implementation assessment and does not reproduce ISO copyrighted control text. Control names are used as identifiers for mapping purposes. Final applicability, risk treatment and SoA approval must be performed by the responsible organization and documented with objective evidence.

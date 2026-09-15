# NEF–G-3–GerChain — Statement of Applicability (SoA)

**Document status:** Draft for controlled review  
**Version:** 0.2  
**ISMS scope:** NEF–G-3–GerChain core infrastructure  
**Technical baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`

## 1. Purpose

This Statement of Applicability (SoA) records the information-security control decisions relevant to the defined ISMS scope. It links risk treatment, organizational controls, technical controls and evidence.

This document is an organization-specific implementation record. It does not reproduce the copyrighted text of ISO/IEC 27001 Annex A.

## 2. Decision status

The following statuses are used:

- **IMPLEMENTED:** evidence indicates the control objective is operating within scope.
- **PARTIALLY IMPLEMENTED:** some technical or organizational elements exist, but evidence or coverage is incomplete.
- **PLANNED:** treatment is defined but implementation/evidence is not complete.
- **NOT APPLICABLE:** formally justified as outside the approved ISMS scope or otherwise not relevant; requires management approval.
- **OPEN:** assessment or evidence is insufficient to make a final decision.

No item is marked final GREEN solely from source-code presence.

## 3. Control applicability register — 93/93 controls addressed

The register below addresses all 93 Annex A controls: A.5 (37), A.6 (8), A.7 (14), A.8 (34). Applicability and implementation decisions remain subject to risk treatment, scope confirmation and management approval.

| Ref | Control area | Applicability | Current status | Main evidence / action |
|---|---|---|---|---|
| A.5.1 | Information-security policies | Yes | PLANNED | ISMS policy suite required |
| A.5.2 | Security roles and responsibilities | Yes | OPEN | Named owners and responsibilities required |
| A.5.3 | Segregation of duties | Yes | OPEN | Role matrix and conflict review required |
| A.5.4 | Management responsibilities | Yes | PLANNED | Management governance evidence required |
| A.5.5 | Contact with authorities | Yes | GAP | Authority/contact register and notification responsibilities required |
| A.5.6 | Contact with special interest groups | Conditional | GAP | Relevant professional/security-group contacts and rationale required |
| A.5.7 | Threat intelligence | Yes | OPEN | Threat-monitoring process required |
| A.5.8 | Security in project management | Yes | PARTIALLY IMPLEMENTED | PR/branch/change governance exists; formal ISMS process required |
| A.5.9 | Information and asset inventory | Yes | PARTIALLY IMPLEMENTED | Asset register created; ownership verification pending |
| A.5.10 | Acceptable use | Yes | PLANNED | Acceptable-use policy required |
| A.5.11 | Return of assets | Yes | PLANNED | Personnel/contractor process required |
| A.5.12 | Information classification | Yes | PARTIALLY IMPLEMENTED | Classification document created; formal approval pending |
| A.5.13 | Information labelling | Yes | PLANNED | Labelling/handling procedure required |
| A.5.14 | Information transfer | Yes | PLANNED | Transfer procedure required |
| A.5.15 | Access control policy | Yes | PARTIALLY IMPLEMENTED | Technical least-privilege principles exist; policy/evidence pending |
| A.5.16 | Identity management | Yes | OPEN | IAM register and lifecycle process required |
| A.5.17 | Authentication information | Yes | OPEN | Credential management and MFA evidence required |
| A.5.18 | Access rights | Yes | OPEN | Periodic access review required |
| A.5.19 | Supplier security | Yes | PLANNED | Supplier register/assessment required |
| A.5.20 | Supplier agreements | Yes | PLANNED | Security clauses and review required |
| A.5.21 | Information security in ICT supply chain | Yes | GAP | ICT supplier-chain risk, requirements and monitoring required |
| A.5.22 | Monitoring/change management of supplier services | Yes | GAP | Supplier-service review, performance/security monitoring and change process required |
| A.5.23 | Cloud service security | Yes/conditional | OPEN | Actual service inventory and responsibility model required |
| A.5.24 | Incident planning | Yes | PLANNED | Incident response procedure required |
| A.5.25 | Incident assessment/decision | Yes | PLANNED | Incident triage process required |
| A.5.26 | Incident response | Yes | PLANNED | Response procedure and exercise required |
| A.5.27 | Incident lessons learned | Yes | PLANNED | Post-incident review process required |
| A.5.28 | Evidence collection | Yes | PARTIALLY IMPLEMENTED | Witness/audit evidence exists; formal procedure pending |
| A.5.29 | Security during disruption | Yes | PLANNED | Continuity requirements required |
| A.5.30 | ICT readiness for continuity | Yes | PARTIALLY IMPLEMENTED | Technical recovery exists; formal continuity evidence pending |
| A.5.31 | Legal/regulatory requirements | Yes | OPEN | Requirements register required |
| A.5.32 | Intellectual-property rights | Yes | OPEN | IP ownership/license register required |
| A.5.33 | Protection of records | Yes | PARTIALLY IMPLEMENTED | Audit/reconciliation records exist; retention policy pending |
| A.5.34 | Privacy/PII protection | Conditional | OPEN | Data inventory and legal applicability assessment required |
| A.5.35 | Independent security review | Yes | OPEN | Independent re-performance required |
| A.5.36 | Compliance with security policies | Yes | PLANNED | Internal audit/control review required |
| A.5.37 | Documented operating procedures | Yes | PARTIALLY IMPLEMENTED | Technical procedures exist; ISMS procedures incomplete |
| A.6.1 | Screening | Yes | OPEN | Personnel process/evidence required |
| A.6.2 | Employment terms | Yes | OPEN | Contractual security requirements required |
| A.6.3 | Awareness and training | Yes | PLANNED | Training programme and records required |
| A.6.4 | Disciplinary process | Yes | OPEN | HR/legal process confirmation required |
| A.6.5 | Responsibilities after termination/change | Yes | OPEN | Offboarding process required |
| A.6.6 | Confidentiality agreements | Yes | OPEN | NDA/contract evidence required |
| A.6.7 | Remote working | Yes | OPEN | Remote-access policy and technical evidence required |
| A.6.8 | Security event reporting | Yes | PLANNED | Reporting mechanism required |
| A.7.1 | Physical security perimeter | Yes | OPEN | Physical environment assessment required |
| A.7.2 | Physical entry | Yes | OPEN | Entry controls/evidence required |
| A.7.3 | Securing offices/facilities | Yes | OPEN | Facility assessment required |
| A.7.4 | Physical monitoring | Yes | OPEN | Applicable monitoring evidence required |
| A.7.5 | Physical/environmental threats | Yes | OPEN | Environmental risk assessment required |
| A.7.6 | Work in secure areas | Yes | OPEN | Procedure required |
| A.7.7 | Clear desk/screen | Yes | PLANNED | Policy required |
| A.7.8 | Equipment placement/protection | Yes | OPEN | Infrastructure assessment required |
| A.7.9 | Off-premises assets | Yes | OPEN | Asset handling process required |
| A.7.10 | Storage media | Yes | PLANNED | Media handling/disposal procedure required |
| A.7.11 | Supporting utilities | Yes | OPEN | Infrastructure dependency assessment required |
| A.7.12 | Cabling | Conditional | OPEN | Physical infrastructure assessment required |
| A.7.13 | Equipment maintenance | Yes | OPEN | Maintenance records/process required |
| A.7.14 | Secure disposal/reuse | Yes | PLANNED | Disposal procedure required |
| A.8.1 | Endpoint devices | Yes | OPEN | Endpoint inventory and security baseline required |
| A.8.2 | Privileged access rights | Yes | OPEN | Privileged account register/MFA required |
| A.8.3 | Information access restriction | Yes | PARTIALLY IMPLEMENTED | Repository/role controls exist; organizational evidence pending |
| A.8.4 | Source-code access | Yes | PARTIALLY IMPLEMENTED | Protected repository and review controls exist |
| A.8.5 | Secure authentication | Yes | OPEN | MFA and authentication evidence required |
| A.8.6 | Capacity management | Yes | OPEN | Capacity thresholds/monitoring required |
| A.8.7 | Malware protection | Yes | OPEN | Endpoint/server protection evidence required |
| A.8.8 | Technical vulnerability management | Yes | PARTIALLY IMPLEMENTED | CodeQL/security checks exist; full vulnerability process required |
| A.8.9 | Configuration management | Yes | PARTIALLY IMPLEMENTED | Git/configuration control exists; formal baseline required |
| A.8.10 | Information deletion | Yes | PLANNED | Retention/deletion procedure required |
| A.8.11 | Data masking | Conditional | OPEN | Data inventory determines applicability |
| A.8.12 | Data leakage prevention | Yes | OPEN | DLP/data-transfer assessment required |
| A.8.13 | Information backup | Yes | OPEN | Backup register and restore evidence required |
| A.8.14 | Redundancy | Yes | OPEN | Availability architecture and evidence required |
| A.8.15 | Logging | Yes | PARTIALLY IMPLEMENTED | Audit/security records exist; retention/monitoring process pending |
| A.8.16 | Monitoring activities | Yes | OPEN | Security monitoring process required |
| A.8.17 | Clock synchronization | Yes | OPEN | Infrastructure configuration evidence required |
| A.8.18 | Privileged utility use | Yes | OPEN | Privileged tooling register/control required |
| A.8.19 | Software installation | Yes | OPEN | Approved software/change process required |
| A.8.20 | Network security | Yes | OPEN | Network architecture/security baseline required |
| A.8.21 | Network services | Yes | OPEN | Service inventory and security requirements required |
| A.8.22 | Network segregation | Yes | OPEN | Architecture/infrastructure assessment required |
| A.8.23 | Web filtering | Conditional | OPEN | Actual endpoint/network scope determines applicability |
| A.8.24 | Cryptography | Yes | PARTIALLY IMPLEMENTED | Cryptographic/decision controls exist; key lifecycle evidence pending |
| A.8.25 | Secure development lifecycle | Yes | PARTIALLY IMPLEMENTED | PR, branch protection and tests exist; formal SDL required |
| A.8.26 | Application security requirements | Yes | PARTIALLY IMPLEMENTED | CORE requirements/tests exist; formal requirements process required |
| A.8.27 | Secure architecture | Yes | PARTIALLY IMPLEMENTED | CORE architecture/evidence exists |
| A.8.28 | Secure coding | Yes | PARTIALLY IMPLEMENTED | Code review/CI/security scanning exist |
| A.8.29 | Security testing | Yes | IMPLEMENTED/PARTIAL | CORE automated validation and CodeQL exist; broader security test programme pending |
| A.8.30 | Outsourced development | Conditional | OPEN | Contractor/supplier assessment required |
| A.8.31 | Separation of development/test/production | Yes | OPEN | Environment inventory and segregation evidence required |
| A.8.32 | Change management | Yes | PARTIALLY IMPLEMENTED | Protected main, PR review and required checks exist |
| A.8.33 | Test information | Yes | OPEN | Test-data classification and handling required |
| A.8.34 | Protection during audit testing | Yes | OPEN | Audit-test procedure and authorization required |

## 4. Three-state interpretation for CORE comparison

For management reporting, the detailed statuses above are normalized as follows:

- **GREEN:** objective evidence shows the control is operating within the defined ISMS scope, with no material evidence gap identified at the current review stage.
- **PARTIAL:** meaningful technical and/or organizational implementation exists, but required governance, evidence, coverage or operating effectiveness is incomplete.
- **GAP:** no sufficient implementation/evidence has been verified, or a required organizational process has not yet been established.

This three-state view is an assessment aid; it does not replace the formal SoA decision, risk treatment, management approval or independent assessment.

## 5. Key interpretation

The technical GerChain CORE controls provide meaningful evidence for several technological and integrity-related areas. However, the SoA remains largely **OPEN/PARTIALLY IMPLEMENTED/GAP** because ISO/IEC 27001 conformity is an organizational ISMS matter.

The following are specifically not declared GREEN until evidence exists:

- organizational IAM/MFA;
- privileged access governance;
- personnel security;
- supplier security and ICT supply-chain controls;
- physical security;
- backup/restore governance;
- incident management;
- internal audit;
- management review;
- independent assurance.

## 6. Applicability principle

Applicability is determined by risk, scope, legal/contractual requirements and organizational context. Annex A is a normative reference set used with the risk treatment process; it is not a blind checklist requiring every control to be implemented identically. Necessary controls must be included in the SoA, while exclusions require justification and approval.

## 7. SoA approval requirements

Before the SoA becomes final, management shall confirm:

1. ISMS scope;
2. asset ownership;
3. risk acceptance criteria;
4. risk treatment decisions;
5. applicability decisions;
6. control implementation responsibilities;
7. evidence requirements.

## 8. Gate

**G4 — Statement of Applicability: OPEN.**

The SoA now addresses all **93/93 Annex A control references**, but it is **not yet a final approved organizational SoA**. The next closure work is to validate each control's applicability, evidence, owner, implementation status and residual risk, then obtain management approval.

# NEF–G-3–GerChain — MNS ISO/IEC 27001:2023 ISMS Scope

**Document status:** Draft for controlled review  
**Version:** 0.1  
**Scope:** Information Security Management System (ISMS) alignment for the NEF–G-3–GerChain core infrastructure  
**GerChain technical baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`  
**Author:** Доржсүрэнгийн Энх-Амгалан

## 1. Purpose

This document defines the proposed scope of the Information Security Management System (ISMS) for the NEF–G-3–GerChain core infrastructure and establishes the controlled basis for subsequent risk assessment, Statement of Applicability, control implementation, evidence retention, internal audit and independent assessment.

This document does not constitute ISO/IEC 27001 certification or an independent conformity assessment.

## 2. ISMS objective

The ISMS shall protect the confidentiality, integrity and availability of information and information-processing capabilities supporting:

1. NEF — digital registration and valuation foundation for assets/wealth;
2. G-3 Escrow — condition-based escrow architecture and assurance model;
3. GerChain CORE — escrow-based value-flow infrastructure;
4. associated architecture, source code, data, cryptographic material, audit evidence, operational records and governance information.

## 3. Scope boundary

### 3.1 Included

The ISMS scope includes, as applicable:

- GerChain CORE source code and controlled development repository;
- CORE application services and supporting components;
- Money Ledger / Money Engine;
- Escrow Engine;
- Witness Chain;
- idempotency and transaction-integrity controls;
- outbox and recovery mechanisms;
- PostgreSQL data stores supporting CORE;
- reconciliation and audit infrastructure;
- cryptographic and decision controls;
- source-control, CI and release-governance processes;
- architecture, technical documentation and security evidence;
- information assets and records necessary to operate, maintain, secure and assure the CORE infrastructure;
- personnel, roles, privileged access and third parties insofar as they affect the scoped information assets;
- backup, recovery, incident management and business-continuity arrangements relevant to the scope.

### 3.2 Explicitly excluded from the current CORE assurance scope

SHUUD application behavior, SHUUD-specific API behavior, SHUUD sandbox behavior and SHUUD-specific end-to-end evidence are excluded from the current GerChain CORE assurance scope unless a future formal scope decision expands the ISMS boundary.

Exclusion from the current CORE scope does not mean SHUUD is inherently insecure; it means that its controls are assessed separately.

## 4. Organizational boundary

The ISMS shall identify the organization responsible for ownership, governance, operation and protection of the scoped information assets. Roles and responsibilities shall be formally assigned before certification readiness is declared.

Where development, hosting, auditing, cloud services or other activities are performed by third parties, the relevant interfaces and security responsibilities shall be documented.

## 5. Information boundary

The scope covers information whose compromise could affect the confidentiality, integrity, availability, authenticity, traceability or accountability of the scoped infrastructure, including:

- source code and build/release information;
- system and database configuration;
- authentication and authorization information;
- cryptographic keys and certificates;
- transaction and escrow records;
- witness and audit records;
- reconciliation records;
- test and validation evidence;
- security logs and incident records;
- architecture and intellectual-property information;
- contracts and security-related third-party information.

Secrets such as private keys, passwords, access tokens and production credentials shall never be stored in this document or committed to the repository.

## 6. Technology boundary

The technology boundary shall be established from the actual operating architecture and shall include relevant development, test, production, backup and recovery environments where they process scoped information.

The frozen GerChain CORE baseline remains unchanged by this documentation work.

## 7. Interested parties and requirements

The ISMS shall identify and periodically review relevant requirements from:

- asset owners and users;
- management and governance bodies;
- financial and business counterparties;
- auditors and independent assessors;
- technology suppliers;
- applicable legal and regulatory authorities;
- contractual obligations;
- information-security and privacy requirements;
- applicable national standards, including MNS ISO/IEC 27001:2023.

## 8. Scope principles

1. Security claims shall be supported by retained evidence.
2. Technical test results shall not be treated as proof of organizational controls unless organizational evidence exists.
3. Controls shall be selected and justified through risk assessment and documented in the Statement of Applicability.
4. Open or missing evidence shall remain open/missing until objectively closed.
5. The scope shall be reviewed when material organizational, technological, legal or business changes occur.

## 9. Certification-readiness statement

At this stage, this document establishes the proposed ISMS boundary only. It does not state that the organization or GerChain CORE is certified or fully conformant with MNS ISO/IEC 27001:2023.

Certification readiness shall be considered only after the ISMS has been implemented, evidence has been retained, internal audit and management review have been completed, corrective actions have been addressed, and an independent conformity assessment has been performed by an appropriate certification body.

## 10. Next controlled documents

The following documents shall be developed in sequence:

1. `ISO27001_INFORMATION_ASSET_REGISTER.md`
2. `ISO27001_INFORMATION_CLASSIFICATION.md`
3. `ISO27001_RISK_ASSESSMENT.md`
4. `ISO27001_RISK_TREATMENT_PLAN.md`
5. `ISO27001_STATEMENT_OF_APPLICABILITY.md`
6. `ISO27001_CONTROL_MATRIX.md`
7. `ISO27001_EVIDENCE_REGISTER.md`
8. IAM/MFA, privileged-access, incident, backup, continuity, supplier and internal-audit procedures.

## 11. Gate

**G1 — ISMS Scope:** OPEN until organizational owner, physical/technology boundaries and interested-party requirements are formally verified.

# NEF–G-3–GerChain — Information Asset Register

**Document status:** Draft for controlled review  
**Version:** 0.1  
**ISMS scope:** NEF–G-3–GerChain core infrastructure  
**GerChain technical baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`

## 1. Purpose

This register identifies information assets and supporting assets that require protection under the proposed ISMS. It is a controlled starting point for risk assessment and the Statement of Applicability.

Asset ownership and classification shall be formally confirmed by the responsible organization before final ISMS approval.

## 2. Classification key

- **OPEN:** may be publicly disclosed when approved.
- **INTERNAL:** intended for authorized organizational use.
- **CONFIDENTIAL:** disclosure requires explicit authorization.
- **HIGHLY CONFIDENTIAL:** compromise could cause severe security, financial, legal or strategic impact.

## 3. Asset register

| ID | Asset | Type | Primary security properties | Proposed classification | Owner | Status |
|---|---|---|---|---|---|---|
| IA-001 | NEF architecture and methodology | Intellectual property / information | C, I | CONFIDENTIAL | To assign | OPEN |
| IA-002 | G-3 Escrow architecture and methodology | Intellectual property / information | C, I | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-003 | GerChain CORE source code | Software / intellectual property | C, I | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-004 | GerChain CORE executable/build artifacts | Software | I, A | CONFIDENTIAL | To assign | OPEN |
| IA-005 | Money Ledger / Money Engine logic | Software | I, A, C | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-006 | Escrow Engine logic | Software | I, A, C | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-007 | Witness Chain logic and records | Software / records | I, A | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-008 | Database schema and migrations | Software / configuration | I, A | CONFIDENTIAL | To assign | OPEN |
| IA-009 | PostgreSQL CORE data | Data | C, I, A | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-010 | Transaction / escrow records | Data / financial records | C, I, A | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-011 | Audit and reconciliation records | Security / audit records | I, A | CONFIDENTIAL | To assign | OPEN |
| IA-012 | Security and application logs | Security records | C, I, A | CONFIDENTIAL | To assign | OPEN |
| IA-013 | Cryptographic private keys | Cryptographic material | C, I | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-014 | API credentials / access tokens | Authentication material | C | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-015 | Database credentials | Authentication material | C | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-016 | Certificates and key metadata | Cryptographic material | C, I | CONFIDENTIAL | To assign | OPEN |
| IA-017 | Git repository and version history | Development infrastructure | I, A, C | CONFIDENTIAL | To assign | OPEN |
| IA-018 | CI/CD configuration and evidence | Development infrastructure | I, A, C | CONFIDENTIAL | To assign | OPEN |
| IA-019 | Architecture diagrams | Documentation | C, I | INTERNAL | To assign | OPEN |
| IA-020 | CORE validation/test evidence | Assurance evidence | I, A | CONFIDENTIAL | To assign | OPEN |
| IA-021 | Audit evidence index and control matrix | Assurance evidence | I, A | CONFIDENTIAL | To assign | OPEN |
| IA-022 | Security policies and procedures | Governance information | I, C | INTERNAL | To assign | OPEN |
| IA-023 | Risk register | Governance information | C, I | CONFIDENTIAL | To assign | OPEN |
| IA-024 | Statement of Applicability | Governance information | I, C | CONFIDENTIAL | To assign | OPEN |
| IA-025 | User identity and access records | Identity information | C, I | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-026 | Privileged access records | Identity/security information | C, I | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-027 | Backup copies | Data / infrastructure | C, I, A | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-028 | Recovery procedures | Operational information | I, A | CONFIDENTIAL | To assign | OPEN |
| IA-029 | Incident records | Security records | C, I | CONFIDENTIAL | To assign | OPEN |
| IA-030 | Supplier/security agreements | Contractual information | C, I | CONFIDENTIAL | To assign | OPEN |
| IA-031 | Employee/contractor security records | Personnel information | C, I | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-032 | Intellectual-property ownership records | Legal/IP information | I, C | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-033 | Third-party/open-source license records | Legal/compliance information | I, C | CONFIDENTIAL | To assign | OPEN |
| IA-034 | Production infrastructure configuration | Infrastructure information | C, I, A | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-035 | Backup/recovery infrastructure | Infrastructure | C, I, A | HIGHLY CONFIDENTIAL | To assign | OPEN |
| IA-036 | Security monitoring configuration | Security infrastructure | C, I, A | CONFIDENTIAL | To assign | OPEN |

## 4. Security-property notation

- **C — Confidentiality:** unauthorized disclosure must be prevented.
- **I — Integrity:** unauthorized alteration or destruction must be prevented or detectable.
- **A — Availability:** authorized users must have access when required.

## 5. Handling rules for highly confidential assets

Highly confidential assets shall not be placed in ordinary presentation packages or removable media unless specifically authorized and protected.

In particular, the following shall never be distributed as ordinary presentation material:

- private keys;
- passwords;
- API tokens;
- production credentials;
- secret configuration;
- unrestricted production database exports.

## 6. Ownership requirement

Every asset marked `To assign` shall receive a formally designated owner. The owner shall be responsible for classification, risk acceptance, protection requirements, periodic review and disposal/retention decisions as applicable.

## 7. Next step

This register shall be reconciled with:

1. the actual deployed architecture;
2. the repository and CI environment;
3. operational infrastructure;
4. contractual and organizational records;
5. the risk register;
6. the Statement of Applicability.

## 8. Gate

**G2 — Information Asset Register: OPEN.**

The register becomes GREEN only after asset completeness, ownership and classification have been formally verified.

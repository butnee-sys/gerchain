# NEF–G-3–GerChain — Information Classification and Handling

**Document status:** Draft for controlled review  
**Version:** 0.1  
**ISMS scope:** NEF–G-3–GerChain core infrastructure

## 1. Purpose

This document defines a uniform classification and handling model for information within the proposed ISMS. Classification shall be based on the potential impact of unauthorized disclosure, alteration, loss or unavailability.

## 2. Classification levels

### OPEN
Information approved for public disclosure.

Examples:
- approved public architecture summaries;
- public presentation material;
- approved public documentation.

Handling:
- may be published after authorization;
- integrity and version must still be controlled.

### INTERNAL
Information intended for authorized organizational use and not intended for unrestricted public distribution.

Examples:
- internal procedures;
- general technical documentation;
- internal work plans.

Handling:
- access limited to authorized personnel;
- distribution through approved channels;
- controlled versioning.

### CONFIDENTIAL
Information whose unauthorized disclosure or modification could cause material operational, financial, legal or competitive harm.

Examples:
- detailed architecture;
- audit evidence;
- risk register;
- CI configuration;
- contracts;
- reconciliation records.

Handling:
- role-based access;
- authorized distribution only;
- secure storage and transfer;
- retention and disposal requirements;
- access and changes recorded where appropriate.

### HIGHLY CONFIDENTIAL
Information whose compromise could cause severe security, financial, legal, strategic or operational impact.

Examples:
- source code;
- private cryptographic keys;
- production credentials;
- privileged access information;
- sensitive production data;
- unrestricted database exports;
- critical intellectual-property records.

Handling:
- strict least-privilege access;
- MFA for privileged access;
- secure secrets/key management;
- encrypted storage and transfer where appropriate;
- no ordinary removable-media distribution;
- access review and audit logging;
- controlled retention and destruction.

## 3. Handling lifecycle

Every scoped information asset shall be controlled throughout:

`Create → Classify → Store → Access → Use → Share → Archive → Retain/Dispose`

## 4. Removable media

Flash drives, external disks, CDs/DVDs and other removable media shall not be used to distribute HIGHLY CONFIDENTIAL information as part of ordinary official presentation packages.

Official presentation media shall contain only approved OPEN, INTERNAL and specifically authorized CONFIDENTIAL material.

The master technical source remains under controlled repository and organizational access. The presentation copy and archive copy shall be managed separately.

## 5. Source-code protection

Full GerChain CORE source code shall be treated as HIGHLY CONFIDENTIAL unless a formal disclosure decision changes its classification.

Technical reviewers, auditors and investors may receive controlled access to selected evidence or source material under appropriate authorization and contractual protection.

## 6. Cryptographic material and secrets

Private keys, passwords, API tokens, production credentials and secret configuration shall never be stored in this document, ordinary presentation packages or unrestricted repository files.

## 7. Reclassification

Classification may be changed when:

- business requirements change;
- a disclosure is approved;
- legal or contractual requirements change;
- information becomes public;
- security impact changes;
- the information is superseded.

Reclassification shall be authorized and recorded.

## 8. Responsibilities

The designated information asset owner is responsible for classification and handling requirements. System administrators and users are responsible for complying with the assigned classification.

Formal role assignments remain to be completed under the ISMS governance work.

## 9. Gate

**G2 supporting control — OPEN.**

GREEN requires confirmation against the actual asset register, owners, access model and organizational policy.

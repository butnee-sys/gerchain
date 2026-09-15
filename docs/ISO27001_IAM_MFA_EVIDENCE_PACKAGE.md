# NEF–G-3–GerChain — IAM / MFA Evidence Package

**Status:** Evidence template — organizational completion required
**Branch:** `docs/iso27001-alignment`

## 1. Objective

Provide objective evidence that identities and access to scoped information systems are uniquely assigned, authorized according to role, protected by appropriate authentication and periodically reviewed.

## 2. Required evidence

### Identity register
- unique account identifier;
- person/role or service identity;
- system/environment;
- owner;
- status (active/inactive);
- approval reference;
- last review date.

### MFA
- systems/accounts requiring MFA;
- MFA enforcement evidence;
- exception register, if any;
- exception approval and expiry;
- periodic verification.

### Access review
- reviewer;
- review date;
- sampled/complete account population;
- changes/removals;
- unresolved exceptions;
- closure evidence.

## 3. GitHub governance linkage

Repository branch protection and required reviews are supporting evidence for development access governance. They do not substitute for the organization's complete identity and MFA register.

## 4. Evidence protection

Do not place passwords, recovery codes, private keys, access tokens or other authentication secrets in this repository.

## 5. Acceptance test

IAM/MFA can move from **MISSING** to **AVAILABLE** only after the responsible owner verifies the controlled evidence set and records the review date and decision.

## 6. Gate

**Current status: MISSING — organizational evidence not yet supplied/verified.**

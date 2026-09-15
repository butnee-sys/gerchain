# NEF–G-3–GerChain — Cryptographic Key Management Evidence Package

**Status:** Evidence template — organizational completion required

## 1. Lifecycle

`Generate → Register → Protect → Distribute → Use → Rotate → Revoke → Archive/Destroy`

## 2. Required evidence

For each production or security-relevant key class, record:

- key identifier/class, never the secret value;
- purpose and environment;
- responsible owner/custodian;
- generation method;
- storage/protection mechanism;
- access authorization;
- rotation period or trigger;
- revocation process;
- backup/recovery treatment where applicable;
- destruction/archive evidence;
- last review.

## 3. Separation

Development, test and production key material shall be separated where applicable. Secrets shall not be committed to source control.

## 4. Incident handling

Compromise or suspected compromise shall trigger controlled revocation, replacement, impact assessment and incident handling.

## 5. Evidence protection

This document must never contain private keys, seed phrases, passwords, API tokens or other secret material.

## 6. Acceptance test

Status may move from **MISSING** to **AVAILABLE** only when the authorized security owner verifies lifecycle evidence and records the review decision.

## 7. Gate

**Current status: MISSING — organizational key custody/lifecycle evidence not yet supplied/verified.**

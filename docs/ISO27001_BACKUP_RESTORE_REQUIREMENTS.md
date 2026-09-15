# NEF–G-3–GerChain — Backup and Restore Requirements

**Status:** Controlled requirements — evidence pending

## 1. Required backup evidence

The organization shall identify, as applicable:

- systems and information requiring backup;
- backup owner;
- backup frequency;
- retention period;
- storage location and protection;
- encryption/access controls;
- backup integrity verification;
- separation from production where appropriate;
- monitoring and failure handling.

## 2. Restore evidence

A restore test shall demonstrate, with dated objective evidence:

`Selected backup → Restore → Integrity check → Application/data verification → Result → Reviewer`

The test shall record any data loss, recovery-time observation or limitation.

## 3. Recovery objectives

Recovery requirements shall be risk-based and formally approved. Where RPO/RTO values are used, they shall be documented for the relevant service or information asset.

## 4. Technical versus organizational evidence

GerChain recovery tests demonstrate technical recovery behavior within their test scope. They do not replace the organization's approved backup policy, asset coverage decision, retention requirements or restore-test governance.

## 5. Evidence owner

A named operational owner and reviewer shall be assigned.

## 6. Gate

**Backup/restore: MISSING — objective operational evidence required.**

# GerChain CORE — Controlled Audit Matrix

This matrix is a controlled working document. It deliberately distinguishes implementation evidence from organizational assurance.

| Control | Requirement | Evidence | Verdict |
|---|---|---|---|
| GC-IDM-001 | Identity / privileged access governance | Organizational IAM/MFA evidence required | MISSING |
| GC-IDM-002 | MFA / privileged account assurance | MFA enforcement and account evidence required | MISSING |
| GC-WIT-002 | Witness integrity / tamper evidence | Witness and DEE security tests | GREEN |
| GC-RES-002 | Release atomicity / idempotency | Atomic release + PostgreSQL concurrency evidence | GREEN |
| GC-RES-003 | Abandoned PROCESSING recovery | Recovery implementation + PostgreSQL tests + PR #63 | GREEN |
| GC-IND-001 | Independent audit/re-performance | Independent re-performance package | OPEN |

## Supporting CORE controls

- Operating DB reconciliation: GREEN.
- PostgreSQL concurrency: GREEN.
- CORE reconciliation CI: GREEN.
- CodeQL: GREEN.
- CORE/SHUUD boundary: GREEN.
- PwC baseline: FROZEN.

## Audit interpretation

`GREEN` means the repository contains traceable technical evidence for the stated control. It does not mean an external auditor has independently attested to the control.

`MISSING` means required evidence is not currently retained.

`OPEN` means the control requires a defined independent or external evidence step before final audit closure.

## Scope boundary

SHUUD application behavior, SHUUD sandbox behavior, SHUUD API behavior, and SHUUD-specific PostgreSQL/E2E evidence are excluded from this CORE matrix unless the formal audit scope is later expanded.

# GerChain CORE — Controlled Audit Matrix

This matrix deliberately distinguishes implementation evidence from organizational assurance.

| Control | Requirement | Evidence | Verdict |
|---|---|---|---|
| GC-IDM-001 | Identity / IAM / MFA governance | Organization-level privileged-account inventory and MFA enforcement evidence | MISSING |
| GC-IDM-002 | Privileged access governance | Role approval, access review, removal and administrative traceability evidence | MISSING |
| GC-WIT-002 | Witness integrity / tamper evidence | Witness and DEE security tests | GREEN |
| GC-RES-002 | Release atomicity / idempotency | Atomic release + PostgreSQL concurrency evidence | GREEN |
| GC-RES-003 | Abandoned PROCESSING recovery | Recovery implementation + PostgreSQL tests + PR #63 | GREEN |
| GC-IND-001 | Independent audit/re-performance | Independent reviewer re-performance package | OPEN |

## Supporting CORE controls

- Operating DB reconciliation: GREEN.
- PostgreSQL concurrency: GREEN.
- CORE reconciliation CI: GREEN.
- CodeQL: GREEN.
- Post-merge main CORE CI: GREEN.
- Main branch governance: GREEN / VERIFIED.
- CORE/SHUUD boundary: GREEN.
- PwC baseline: FROZEN.

## Audit interpretation

`GREEN` means traceable evidence is retained for the stated control. It does not mean an external auditor has independently attested to the control.

`MISSING` means required evidence is not currently retained.

`OPEN` means an independent or external evidence step remains before final audit closure.

## Scope boundary

SHUUD application behavior, SHUUD sandbox behavior, SHUUD API behavior, and SHUUD-specific PostgreSQL/E2E evidence are excluded from this CORE matrix unless the formal audit scope is expanded.

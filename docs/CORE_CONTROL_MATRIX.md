# GerChain CORE — Controlled Audit Matrix

This matrix is a controlled working document. It deliberately distinguishes implementation evidence from organizational assurance.

| Control | Requirement | Evidence | Verdict |
|---|---|---|---|
| GC-IDM-001 | Identity / privileged access governance | Organizational IAM/MFA evidence required | MISSING |
| GC-IDM-002 | MFA / privileged account assurance | MFA enforcement and account evidence required | MISSING |
| GC-WIT-002 | Witness integrity / tamper evidence | Witness and DEE security tests | GREEN |
| GC-RES-002 | Value-movement atomicity / idempotency | Canonical Ledger transaction boundary + PostgreSQL production gate + replay evidence | GREEN |
| GC-RES-003 | Abandoned PROCESSING recovery | Recovery implementation + PostgreSQL tests + PR #63 | GREEN |
| GC-IND-001 | Independent audit/re-performance | Independent PostgreSQL persisted-value verification + production re-performance | OPEN — no independent report/artifact verified |

## Supporting CORE controls

- Operating DB reconciliation: GREEN.
- Canonical Ledger PostgreSQL concurrency: GREEN — fresh production gate and migration serialization evidence recorded.
- CORE/fundamental-architecture CI: UNVERIFIED for the production-entrypoint correction SHA; no completed-success exact-SHA run verified in the latest check.
- CodeQL: UNVERIFIED for the production-entrypoint correction SHA; exact-SHA completion evidence not verified.
- CORE/SHUUD boundary: GREEN.
- PwC baseline: FROZEN.

## Audit interpretation

`GREEN` means the repository contains traceable technical evidence for the stated control. It does not mean an external auditor has independently attested to the control.

`MISSING` means required evidence is not currently retained.

`OPEN` means the control requires a defined independent or external evidence step before final audit closure.

## Scope boundary

SHUUD application behavior, SHUUD sandbox behavior, SHUUD API behavior, and SHUUD-specific PostgreSQL/E2E evidence are excluded from this CORE matrix unless the formal audit scope is later expanded.


## Exact-SHA governance and production evidence review — 2026-10-12

**Reviewed code SHA:** `e860f502f3e1a2d56fd873ad2faab7b1ab630740`  
**Evidence Index update commit:** `46dd2be2cc1b8f63848dcf52e49bab822354cba4`  
**Decision:** **BLOCKED / NOT LOCKED**.

| Control | Current verdict | Closure evidence required |
|---|---|---|
| GC-IDM-001 Identity / privileged access governance | MISSING | Named privileged-account inventory, role/least-privilege map, approval owner, periodic review evidence, removal/offboarding evidence |
| GC-IDM-002 MFA / privileged account assurance | MISSING | Enforced MFA policy and machine-verifiable organization/repository account evidence; do not rely on narrative assertion alone |
| GC-GOV-003 Main branch protection | UNVERIFIED | Repository ruleset/branch-protection export showing required reviews, required status checks, stale approval handling, and restriction of force-push/deletion |
| GC-CI-001 Exact-SHA production and core gates | UNVERIFIED | All authoritative required jobs completed successfully against the same SHA, with job logs and required artifacts retained |
| GC-IND-001 Independent re-performance | OPEN | Independent reviewer report and reproduced PostgreSQL boot, lifecycle, reconciliation, recovery and legacy-authority checks |
| GC-LEG-001 Legacy value-authority isolation | OPEN | Static call-path inventory plus tests proving legacy SQLite, MoneyLedger, ReleaseAccount, AccountBalance, and application-owned balance paths cannot mutate production truth |

### Exact-SHA machine status observed

For `e860f502f3e1a2d56fd873ad2faab7b1ab630740`, the combined commit status endpoint returned one status: `security/snyk (butnee-sys) = success`. No completed-success production PostgreSQL, full-suite, core-gates, CodeQL, or independent-re-performance run was verified in this check. This is **not** a full green result.

### Lock rule

Do not change any control above to GREEN based on implementation alone, a queued run, a prior SHA, or the single Snyk status. Organizational controls require organizational evidence. Independent re-performance must be performed by a person/team independent of the implementation. Final lock remains withheld until every mandatory gate is evidenced against the exact audited SHA.

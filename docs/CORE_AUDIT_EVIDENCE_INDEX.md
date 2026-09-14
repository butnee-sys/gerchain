# GerChain CORE — Audit Evidence Index

**Audit scope:** GerChain CORE  
**Frozen baseline:** `274f45c83ce088e2229a2628e3a80403a68503df`  
**Current technical baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`

## Evidence register

| Evidence ID | Area | Evidence location | Status |
|---|---|---|---|
| E-CORE-001 | Atomic release / idempotency | `persistence/atomic_release.py` + CORE tests | GREEN |
| E-CORE-002 | PostgreSQL concurrency | `.github/workflows/postgres-concurrency.yml` + PostgreSQL tests; PR #67 | GREEN |
| E-CORE-003 | Abandoned `PROCESSING` recovery | `persistence/atomic_release.py` + recovery tests; PR #63 | GREEN |
| E-CORE-004 | Operating reconciliation | `persistence/reconciliation.py` + tests; PR #64 | GREEN |
| E-CORE-005 | CORE reconciliation CI | `.github/workflows/core-reconciliation.yml` | GREEN |
| E-CORE-006 | DEE key management | `tests/test_dee_key_management.py` | GREEN |
| E-CORE-007 | DEE security | `tests/test_dee_security.py` | GREEN |
| E-CORE-008 | CORE/SHUUD boundary | CORE-only PostgreSQL workflow + scope-boundary evidence; PR #67 | GREEN |
| E-CORE-009 | CodeQL | `.github/workflows/codeql.yml` + successful run evidence | GREEN |
| E-CORE-010 | PwC frozen baseline | Frozen SHA and prior PwC evidence set | FROZEN |
| E-CI-001 | Post-merge main CORE CI | Main commit `621e7e2...` successful CORE workflow runs | GREEN |
| E-GOV-003 | Main branch governance | Active `CORE-main-protection` ruleset ID `23342561`; required CORE checks | GREEN / VERIFIED |
| E-GOV-001 | IAM / MFA | Organizational IAM/MFA evidence package | MISSING |
| E-GOV-002 | Privileged access review | Organizational role inventory/review/access records | MISSING |
| E-IND-001 | Independent re-performance | Independent reviewer signed re-performance record | OPEN |

## Evidence retention rule

For final audit submission, retain workflow run IDs, job summaries, test output, audited commit SHA, pull-request merge records, ruleset verification, and organizational evidence outside GitHub in the designated audit evidence repository.

## Evidence quality rule

Evidence must be traceable, dated, scope-specific, and tied to the audited software version. Screenshots or narrative statements alone are not sufficient where machine-verifiable evidence is available.

## Final closure rule

`GC-IDM-001`, `GC-IDM-002`, and `GC-IND-001` remain the only material open closure gates in the current CORE audit record. They must be evidenced or formally accepted as audit exceptions before final lock.

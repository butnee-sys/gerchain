# GerChain CORE — Audit Evidence Index

**Audit scope:** GerChain CORE  
**Frozen baseline:** `274f45c83ce088e2229a2628e3a80403a68503df`  
**Current W3 execution baseline:** `46f9443a6a4e14e91807f75a7dd9fae619ad7131`

## Evidence register

| Evidence ID | Area | Evidence location | Status |
|---|---|---|---|
| E-CORE-001 | Atomic release / idempotency | `persistence/atomic_release.py` + CORE tests | GREEN |
| E-CORE-002 | PostgreSQL concurrency | `.github/workflows/postgres-concurrency.yml` + PostgreSQL tests; PR #67 | GREEN |
| E-CORE-003 | Abandoned `PROCESSING` recovery | `persistence/atomic_release.py` + recovery tests; PR #63 | GREEN |
| E-CORE-004 | Operating reconciliation | `persistence/reconciliation.py` + `tests/test_operating_reconciliation.py`; PR #64 | GREEN |
| E-CORE-005 | CORE reconciliation CI | `.github/workflows/core-reconciliation.yml` | GREEN |
| E-CORE-006 | DEE key management | `tests/test_dee_key_management.py` | GREEN |
| E-CORE-007 | DEE security | `tests/test_dee_security.py` | GREEN |
| E-CORE-008 | CORE/SHUUD boundary | CORE-only PostgreSQL workflow + scope-boundary evidence; PR #67 | GREEN |
| E-CORE-009 | CodeQL | `.github/workflows/codeql.yml` + successful run evidence | GREEN |
| E-CORE-010 | PwC frozen baseline | Frozen SHA and prior PwC evidence set | FROZEN |
| E-CORE-011 | W3 schema/version authority | `docs/evidence/W3_CLOSURE_2026-09-16.md` + run `35124401671` | GREEN (bounded) |
| E-GOV-001 | IAM / MFA | `GC-IDM-001/002` evidence package | MISSING |
| E-GOV-002 | Privileged access review | Organizational access inventory/review records | MISSING |
| E-GOV-003 | Main branch governance | Branch protection/ruleset evidence | UNVERIFIED |
| E-CI-001 | Post-merge main CI | Merge commit `62594d16...` workflow association | UNVERIFIED |

## W3 closure evidence

W3 execution commit `46f9443a6a4e14e91807f75a7dd9fae619ad7131` passed the CORE W3 production tests, independent oracle/deterministic reproduction, and independent PostgreSQL re-performance in `core-gates` run `35124401671`. The same execution also passed the existing CORE structure tests, W2 C2/C6 regression, and independent W2 PostgreSQL re-performance. Related checks: Operating Reconciliation `35124401691`, PostgreSQL Concurrency `35124401798`, CodeQL `35124401661`, and Snyk success status.

W3 closure is bounded to canonical schema/version authority and concurrency transition semantics. Complete production DDL migration execution remains a separate architectural concern.

## Evidence retention rule

For final audit submission, retain the relevant workflow run IDs, job summaries, test output, commit SHA, pull-request merge record, and any organizational evidence outside GitHub in the designated audit evidence repository.

## Evidence quality rule

Evidence must be traceable, dated, scope-specific, and tied to the audited software version. Screenshots or narrative statements alone are not sufficient where machine-verifiable evidence is available.

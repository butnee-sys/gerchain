# GerChain CORE — Audit Evidence Index

**Audit scope:** GerChain CORE
**Frozen baseline:** `274f45c83ce088e2229a2628e3a80403a68503df`
**Current technical baseline:** `62594d16e926aa084c73f326eb77445d57fd4267`

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
| E-GOV-001 | IAM / MFA | `GC-IDM-001/002` evidence package | MISSING |
| E-GOV-002 | Privileged access review | Organizational access inventory/review records | MISSING |
| E-GOV-003 | Main branch governance | Branch protection/ruleset evidence | UNVERIFIED |
| E-CI-001 | Post-merge main CI | Merge commit `62594d16...` workflow association | UNVERIFIED |

## Evidence retention rule

For final audit submission, retain the relevant workflow run IDs, job summaries, test output, commit SHA, pull-request merge record, and any organizational evidence outside GitHub in the designated audit evidence repository.

## Evidence quality rule

Evidence must be traceable, dated, scope-specific, and tied to the audited software version. Screenshots or narrative statements alone are not sufficient where machine-verifiable evidence is available.

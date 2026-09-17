# GerChain CORE — Audit Evidence Index

**Audit scope:** GerChain CORE  
**Frozen baseline:** `274f45c83ce088e2229a2628e3a80403a68503df`  
**Main baseline:** `621e7e2acefe243d4c72e783970e1eb833c60b96`  
**Current CORE revalidation/evidence commit:** `8258c2dcebfff677291ed85af17648a1176b5993`

## Evidence register

| Evidence ID | Area | Evidence location | Status |
|---|---|---|---|
| E-CORE-001 | Atomic release / idempotency | `persistence/atomic_release.py` + CORE tests | GREEN |
| E-CORE-002 | PostgreSQL concurrency | `.github/workflows/postgres-concurrency.yml` + PostgreSQL tests | GREEN |
| E-CORE-003 | Abandoned `PROCESSING` recovery | `persistence/atomic_release.py` + recovery tests | GREEN |
| E-CORE-004 | Operating reconciliation | `persistence/reconciliation.py` + integration tests | GREEN |
| E-CORE-005 | CORE reconciliation CI | `.github/workflows/core-reconciliation.yml` | GREEN |
| E-CORE-006 | DEE key management | `tests/test_dee_key_management.py` | GREEN |
| E-CORE-007 | DEE security | `tests/test_dee_security.py` | GREEN |
| E-CORE-008 | CORE/SHUUD boundary | CORE-only workflow + scope-boundary evidence | GREEN |
| E-CORE-009 | CodeQL | `.github/workflows/codeql.yml` + current successful run | GREEN |
| E-CORE-010 | PwC frozen baseline | Frozen SHA and prior PwC evidence set | FROZEN |
| E-CORE-011 | W3 schema/version authority | `docs/evidence/W3_CLOSURE_2026-09-16.md` + current CORE gates | GREEN (bounded) |
| E-CORE-012 | W3.1 logical PostgreSQL schema truth | `docs/evidence/W3_1_CLOSURE_2026-09-17.md` + exact execution commit `2d063f6b816a08899ee9f7f12cedf50322ea7099` | GREEN (bounded) |
| E-GOV-001 | IAM / MFA | `GC-IDM-001/002` evidence package | MISSING |
| E-GOV-002 | Privileged access review | Organizational access inventory/review records | MISSING |
| E-GOV-003 | Main branch governance | Active repository ruleset `CORE-main-protection` | VERIFIED (bounded) |
| E-CI-001 | Post-merge main CI | To be captured after final merge | PENDING |
| E-W3-ARCH-001 | Production DDL migration execution | Migration executor assurance package | OPEN |

## Current CORE revalidation evidence

W3.1-A technical closure is recorded at `docs/evidence/W3_1_CLOSURE_2026-09-17.md`. Its exact execution commit is `2d063f6b816a08899ee9f7f12cedf50322ea7099`; the evidence-record refresh is committed at `8258c2dcebfff677291ed85af17648a1176b5993`.

The exact W3.1 execution chain passed CORE structure/boundary, W2, W3, W3.1 logical-schema oracle, independent PostgreSQL W3.1 re-performance, cross-agreement, CORE Operating Reconciliation and CodeQL. The W3.1 closure is bounded to the declared PostgreSQL logical-schema domain and does not close production DDL migration execution.

## Evidence retention rule

For final audit submission, retain the relevant workflow run IDs, job summaries, test output, commit SHA, pull-request merge record, and any organizational evidence outside GitHub in the designated audit evidence repository.

## Evidence quality rule

Evidence must be traceable, dated, scope-specific, and tied to the audited software version. Screenshots or narrative statements alone are not sufficient where machine-verifiable evidence is available.

## Scope rule

SHUUD application behavior, SHUUD sandbox behavior, SHUUD API behavior, and SHUUD-specific PostgreSQL/E2E evidence are excluded from this CORE evidence register.

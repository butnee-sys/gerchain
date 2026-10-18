# FINAL LOCK — Previously Verified Work Register

**Status:** FINAL LOCK — VERIFIED SUBSET ONLY  
**Repository:** `butnee-sys/gerchain`  
**Branch at lock creation:** `feat/ea21-transaction-aware-ledger`  
**Purpose:** Preserve and lock previously evidenced GREEN work without restarting its implementation or falsely promoting unresolved controls.

## 1. Lock decision

The following previously evidenced technical controls are accepted as **LOCKED within their documented scope**. Their implementation/evidence must not be silently discarded, reclassified, or redesigned. Any change requires a reviewed change proposal and fresh evidence for the changed surface.

| Evidence ID / control | Locked disposition | Evidence basis |
|---|---|---|
| E-CORE-001 Atomic release / idempotency | LOCKED — prior GREEN | `persistence/atomic_release.py` and dedicated CORE tests |
| E-CORE-002 PostgreSQL concurrency | LOCKED — prior GREEN | `.github/workflows/postgres-concurrency.yml`, PostgreSQL tests, PR #67 as recorded in the evidence index |
| E-CORE-003 Abandoned PROCESSING recovery | LOCKED — prior GREEN | `persistence/atomic_release.py`, recovery tests, PR #63 as recorded |
| E-CORE-004 Operating reconciliation | LOCKED — prior GREEN | `persistence/reconciliation.py`, `tests/test_operating_reconciliation.py`, PR #64 as recorded |
| E-CORE-005 CORE reconciliation CI design | LOCKED — prior GREEN | `.github/workflows/core-reconciliation.yml` |
| E-CORE-006 DEE key management | LOCKED — prior GREEN | `tests/test_dee_key_management.py` |
| E-CORE-007 DEE security | LOCKED — prior GREEN | `tests/test_dee_security.py` |
| E-CORE-008 CORE scope boundary | LOCKED — prior GREEN, documented scope only | CORE-only PostgreSQL workflow and boundary evidence as recorded |
| E-CORE-009 CodeQL control implementation/evidence set | LOCKED — prior GREEN, historical run scope only | `.github/workflows/codeql.yml` and recorded successful run evidence |
| E-CORE-010 PwC baseline | FROZEN | Frozen baseline SHA recorded in the existing audit documents |
| Canonical DE/DEE/G-3/NEF/GerChain/EXIM/I2B architecture | FROZEN | `docs/DEE_ARCHITECTURE_FREEZE.md`, freeze date 2026-09-14 |
| Canonical Ledger authority design and legacy authority prohibition | DESIGN FROZEN; runtime closure not implied | `docs/EA34_LEGACY_VALUE_AUTHORITY_FREEZE.md` |

## 2. Scope and non-claims

This register locks the previously documented GREEN technical work **at the evidence scope where it was originally accepted**. It does not claim that a historical successful workflow proves the latest commit, or that unit/integration evidence equals production PostgreSQL deployment evidence.

The following remain **OPEN / MISSING / UNVERIFIED** and are explicitly outside this FINAL LOCK:

- Organizational IAM/MFA evidence: `GC-IDM-001`, `GC-IDM-002`.
- Privileged-access review evidence: `E-GOV-002`.
- Main-branch governance and exact-commit CI/security checks where current evidence is unverified.
- Independent audit/re-performance: `GC-IND-001`.
- Production PostgreSQL migration completeness, boot, readiness/health, restart/recovery, and exact-commit re-performance for the latest production-entrypoint/canonical-ledger changes.
- Deep cross-store value-truth reconciliation against a real production-like PostgreSQL dataset.
- Physical read-only enforcement/removal of legacy value stores.

## 3. Canonical invariants protected by this lock

1. Canonical architecture changes require an explicit reviewed architecture-change proposal.
2. No production value mutation outside the Canonical Ledger mutation boundary.
3. No second authoritative Ledger, Witness Chain, Escrow Engine, or application-owned value truth.
4. No direct value release: Decision → Authorization → Release remains mandatory.
5. Unknown or unresolved required conditions are not PASS; fail closed.
6. One-time value movement must be atomic and idempotent.
7. Recovery must not duplicate value movement.
8. Balance equality alone is not sufficient proof of value-truth equality.
9. Historical GREEN evidence is preserved as historical evidence and is not silently promoted to current-SHA proof.

## 4. Change control

Any change to a locked control or canonical invariant must include:
- the exact changed files and commit;
- reason and scope;
- regression tests;
- relevant PostgreSQL evidence where the control is database-dependent;
- impact assessment against the frozen architecture;
- explicit approval before replacing this register's locked disposition.

A code change alone does not reopen unrelated locked work. Reopen only the affected control(s), plus dependent controls demonstrated by impact analysis.

## 5. Overall project status

**FINAL LOCK applies to the previously evidenced subset above.**

**Overall production readiness: NOT LOCKED.**  
**EA-35 deep value-truth reconciliation and current production re-performance: IN PROGRESS / NOT LOCKED.**

This distinction is intentional: preserve what was already proven, and do not misrepresent what has not yet been proven.

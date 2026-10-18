# MASTER PRODUCTION WORK PLAN — STEP 2
## Error / Duplicate / Excess Review and Disposition

**Status:** CLOSED — REVIEW COMPLETE  
**Branch:** `feat/ea21-transaction-aware-ledger`  
**Review target at recording:** `e860f502f3e1a2d56fd873ad2faab7b1ab630740`  
**Recorded:** 2026-10-19  
**Scope:** Fundamental architecture + EAI (Escrow as Infrastructure). Product/application layers remain out of scope.

## 1. Closure definition

Step 2 is the repository-level review and disposition of known errors, duplicate authorities, excess/legacy paths, and boundary violations found during Step 1 inventory. It is not a claim that every legacy table has been physically deleted, every production migration has passed, or overall production readiness is locked. Those are implementation and release gates tracked separately.

## 2. Findings and final disposition

| ID | Finding | Required invariant | Disposition at Step 2 close | Residual gate |
|---|---|---|---|---|
| S2-01 | Multiple balance authorities: `MoneyLedger`, `ReleaseAccount`, `AccountBalance`, and Canonical Ledger | One authoritative production value store | Canonical authority designated as `gerchain_ledger_accounts` + `gerchain_ledger_movements`; legacy stores classified non-authoritative | Physical freeze/archive/removal and migration proof |
| S2-02 | Legacy release persistence could compete with Canonical Ledger | One value-movement boundary | Production runtime factory corrected to configure Canonical Ledger; legacy release path not selected by canonical factory | Exact-SHA PostgreSQL lifecycle/restart proof |
| S2-03 | Legacy API directly mutated SQLite escrow state | No direct downstream mutation of protected truth | Identified mutation endpoints fail closed with HTTP 410 | Verify current-tip tests and route reachability in CI |
| S2-04 | Web UI could mutate application-owned balance state | No application-owned value authority | Legacy transfer mutation endpoint fails closed with HTTP 410 | Verify current-tip tests and production exposure |
| S2-05 | In-memory CLI/server could be mistaken for production runtime | Production entrypoint must establish PostgreSQL canonical authority | `production_entrypoint.py` now constructs `ProductionRuntimeConfig`, instantiates `ProductionRuntimeFactory`, then calls instance `create()` and checks canonical authority | Exact-SHA boot and health/readiness evidence |
| S2-06 | Factory/entrypoint API mismatch | Entrypoint must match actual factory contract | Corrected source-level mismatch; factory initialization targets canonical persistence metadata and configures canonical ledger | Run tests and PostgreSQL execution on exact current SHA |
| S2-07 | `metadata.create_all()` could be confused with production migrations | Existing-schema upgrades require versioned migration evidence | Explicitly classified as insufficient by itself; versioned migration history and schema guard are mandatory | Clean install + supported prior-schema upgrade proof |
| S2-08 | Escrow, movement, witness, outbox and idempotency could diverge | One atomic transaction and one evidence graph | Deep reconciliation contract binds movement to escrow, witness, operation-matched outbox, idempotency and integrity hash; state-only LOCK is treated separately from value movement | Same-SHA PostgreSQL failure/replay/recovery evidence |
| S2-09 | Outbox event could have correct transaction ID but wrong operation/aggregate | Evidence must match the actual movement | Reconciliation checks aggregate ID and `GERCHAIN_{operation}` event type | Maintain negative-path tests in current CI |
| S2-10 | State-only idempotency could be falsely flagged as orphaned | Do not infer operation type absent durable evidence | Reverse orphan-idempotency check is not used where schema does not encode operation type; avoids false positive while movement-side evidence checks remain | Add explicit operation discriminator before any stronger reverse check |
| S2-11 | Legacy SQLite and in-memory stores remain present | No silent fallback to legacy authority | Classified non-authoritative; production must fail closed | Physical read-only freeze/archive/removal remains a separate gate |
| S2-12 | Historical successful CI evidence may be mistaken for current-tip proof | Evidence must match exact SHA | Historical runs remain tied to their recorded SHA; Snyk success alone is not full CI or production proof | Refresh all mandatory workflows on exact target SHA |

## 3. Duplicate / excess disposition

### Authoritative
- Asset registration, valuation and verification truth: NEF.
- Operational value-flow truth: Canonical Ledger in GerChain.
- Escrow condition/governance policy: G-3.
- One authoritative Witness path.
- One authoritative production Outbox path.
- One durable idempotency path per operation.
- One explicit adapter at each canonical boundary.

### Non-authoritative / legacy
- `MoneyLedger` in-memory balances.
- `ReleaseAccount` and `AccountBalance` legacy balance stores.
- Legacy `ReleaseEscrow`, `ReleaseWitness`, and settlement movement representations where retained.
- SQLite balance/escrow stores.
- Legacy in-memory API/CLI runtime.
- Application-owned balance mutation paths, which must remain fail-closed.

No new canonical layer, second ledger, second escrow engine, second witness chain, or application-owned infrastructure truth is authorized.

## 4. Step 2 exit checklist

- [x] Duplicate authorities identified and assigned one canonical owner.
- [x] Known bypasses and legacy mutation surfaces identified and assigned fail-closed disposition.
- [x] Production entrypoint/factory contract mismatch identified and corrected in source.
- [x] Schema initialization versus versioned migration distinction recorded.
- [x] Deep value-truth evidence requirements defined.
- [x] False-positive risk for state-only idempotency documented and dispositioned.
- [x] Residual work assigned to explicit implementation / runtime / independent assurance gates.
- [x] Findings added to the master FINAL LOCK record.
- [ ] Current-tip full CI and PostgreSQL execution — not a Step 2 review prerequisite; remains a production release gate.
- [ ] Physical legacy-store removal/archive — remediation/release gate, not a reason to leave the review itself open.

## 5. Final disposition

**STEP 2 — ERROR / DUPLICATE / EXCESS REVIEW: CLOSED.**

This closes the review and classification step only. It does not mark the implementation remediations as all complete, and does not authorize production release.

**Overall production FINAL LOCK: NOT GRANTED** until exact-SHA CI, PostgreSQL migration/boot, full lifecycle, deep reconciliation, restart/recovery, security/governance, and independent re-performance evidence all satisfy the master lock criteria.

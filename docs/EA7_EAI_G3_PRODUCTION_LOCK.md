# EA-7 — EAI / G-3 Production Lock Record

**Scope:** Step 7 only — EAI / G-3 Escrow Foundation  
**Status:** ARCHITECTURE CONTRACT LOCKED; PRODUCTION READINESS CONDITIONALLY VERIFIED; OVERALL FUNDAMENTAL INFRASTRUCTURE NOT LOCKED BY THIS RECORD  
**Canonical repository:** `butnee-sys/gerchain`  
**Canonical architecture:** `docs/DEE_ARCHITECTURE_FREEZE.md`

## 1. Scope boundary

This lock applies only to the EAI / G-3 Escrow Foundation contract and its integration boundary. It does not reopen or redesign the frozen canonical architecture. It does not lock the entire production infrastructure, database migration history, operational IAM/MFA, branch governance, or independent assurance package.

SHUUD is a separate, isolated application. It is not a G-3 engine, not part of EAI, and not evidence for the production readiness of the fundamental infrastructure. Its only published integration boundary remains EXIM Port.

## 2. Canonical definitions

- **EAI — Escrow as Infrastructure:** escrow is a trust-conditioned economic infrastructure, not merely a tool or a standalone service.
- **G-3 — Escrow Foundation:** the frozen foundation that expresses and governs escrow conditions.
- **G-3 Trinity:** Trust + Transparency + Performance. All required dimensions must pass before value release.
- **Canonical operational authority:** GerChain Core and its single Canonical Ledger / Escrow / Witness / Outbox path.
- **G-3 is policy owner; Core is operational authority.** G-3 must not duplicate Decision, Authorization, Release, Settlement, Reconciliation, Ledger, or Witness engines.

## 3. Locked invariants

1. EAI is a design/operating principle, not a new architecture layer or a second escrow engine.
2. G-3 defines and validates condition, escrow, and governance policy; it does not mutate canonical value truth directly.
3. G-3-to-Core communication uses the explicit `G3ToCoreBoundaryAdapter` contract.
4. The adapter fails closed on invalid request type, missing activity, missing or malformed asset, condition policy, or escrow payload.
5. The asset reference must include `asset_id`.
6. The Core handler is injected through the composition root; G-3 must not import or instantiate a duplicate Core engine.
7. Decision → Authorization → Release remains mandatory.
8. Trust, Transparency, and Performance must all pass; unknown or unresolved mandatory conditions are not a pass.
9. One authoritative Canonical Ledger, one authoritative escrow state machine, one witness path, and one production outbox remain mandatory.
10. No downstream actor, including an application, may directly mutate authoritative value truth, policy, authority, or core execution state.
11. No SHUUD implementation or success signal may be used to satisfy an EAI/G-3 production gate.

## 4. Evidence reviewed

### Architecture and boundary evidence

- Frozen architecture document: `docs/DEE_ARCHITECTURE_FREEZE.md`.
- G-3/Core adapter implementation: `architecture/g3_core.py`.
- Canonical composition root: `architecture/composition_root.py`.
- Production runtime factory: `services/gerchain_runtime_factory.py`.
- Runtime value-authority audit: `docs/EA34_RUNTIME_VALUE_AUTHORITY_AUDIT.md`.

### PostgreSQL evidence recorded in repository

The runtime audit records successful PostgreSQL/EAI verification runs against exact historical candidate commits, including:
- PostgreSQL production re-performance run `37463305181`
- PostgreSQL production gate run `37463305107`
- EAI PostgreSQL Production Proof run `37463304934`
- independent PostgreSQL evidence run `37463304855`

The audit records those runs as successful for commit `f11fcb6411f1458c7bb4696566a695a52141b0c3`. These are historical evidence for that exact SHA, not a claim that the present branch tip has the same CI state.

## 5. Acceptance result

| Control | Result | Interpretation |
|---|---|---|
| EAI/G-3 conceptual boundary | LOCKED | No new layer or duplicate escrow engine |
| G-3/Core adapter design | LOCKED | Explicit adapter; Core authority preserved |
| Trinity release prerequisite | LOCKED | Trust + Transparency + Performance are mandatory |
| Canonical Ledger authority | LOCKED as architecture invariant | Runtime evidence must remain SHA-specific |
| SHUUD isolation | LOCKED as architecture invariant | Separate app; EXIM Port boundary only |
| Historical PostgreSQL/EAI proof | VERIFIED for recorded SHA | Not transferable automatically to later SHAs |
| Current branch-tip CI | NOT VERIFIED by this record | Must not be represented as green |
| Whole infrastructure production lock | NOT GRANTED by this record | Other master-plan gates remain outside Step 7 |

## 6. Final lock decision

**EA-7 EAI/G-3 ARCHITECTURE CONTRACT: FINAL LOCK.**

The contract and scope boundaries above are frozen. Any change requires an explicit architecture-change proposal and review; routine implementation must conform to this record.

**Production status wording permitted:** “EAI/G-3 architecture contract locked; historical PostgreSQL/EAI production proof recorded for the cited commit.”

**Production status wording not permitted from this record alone:** “The entire fundamental infrastructure is production-ready and finally locked,” or “the current branch tip is green.”

This distinction is mandatory: an architecture lock is not a substitute for fresh exact-SHA CI, migration-upgrade proof, recovery/restart evidence, operational IAM/MFA, branch governance, and independent re-performance for the whole infrastructure.

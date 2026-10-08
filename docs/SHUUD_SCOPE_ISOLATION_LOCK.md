# SHUUD Scope Isolation Lock

**Status:** ISOLATED — OUTSIDE FUNDAMENTAL INFRASTRUCTURE PRODUCTION GATE

## Scope decision

SHUUD is a separate application/runtime object. It is not part of the fundamental infrastructure production-readiness target.

The fundamental infrastructure target is limited to:

- Canonical DE / DEE / G-3 boundaries
- NEF + GerChain core infrastructure
- EAI / G-3 escrow-as-infrastructure foundation
- canonical value-flow, authority, evidence, recovery, security and production controls

SHUUD must not be used as evidence of production readiness for these components.

## Isolation invariants

1. SHUUD has no direct imports from canonical GerChain core/service/architecture namespaces.
2. SHUUD does not live as a canonical service module.
3. SHUUD does not use the legacy `shuud.integration` dependency.
4. EXIM Port is the published SHUUD integration boundary.
5. SHUUD sandbox has its own Docker composition and runtime.
6. SHUUD is not the GerChain production entrypoint.
7. SHUUD cannot become an alternate value authority.
8. SHUUD workflow success/failure is not a fundamental-infrastructure production gate.

## Evidence

Primary architecture reference:

`docs/DEE_ARCHITECTURE_FREEZE.md` §1A explicitly defines SHUUD as outside the fundamental infrastructure.

Isolation test:

`tests/test_shuud_exim_boundary.py`

Independent workflows:

- `.github/workflows/shuud-command-layer.yml`
- `.github/workflows/shuud-sandbox-smoke.yml`

Fundamental architecture workflow:

- `.github/workflows/core-gates.yml`

The fundamental workflow does not execute SHUUD application/sandbox lifecycle tests.

## Closure rule

SHUUD may be developed and verified independently after the fundamental infrastructure gate. Its status must never be conflated with the production status of the fundamental infrastructure.

**Canonical scope:** FUNDAMENTAL INFRASTRUCTURE + EAI  
**Separate object:** SHUUD

# Additive Architecture Extensions Proposal v1

**Status:** PROPOSAL — additive only; not part of the canonical freeze  
**Base architecture freeze:** `docs/DEE_ARCHITECTURE_FREEZE.md` at `10a408dc4a7821db85a9bc68cfccdb66a20b4dcf`  
**Scope:** documentation-only proposal. This file does not alter or supersede the frozen architecture.

## 1. Non-negotiable preservation rule

The existing canonical architecture remains unchanged:

`DE → DE Adapter → DEE → DEE↔G-3 Adapter → G-3 → G-3↔Core Adapter → NEF + GerChain Core → Core↔EXIM Adapter → EXIM Port → EXIM↔I2B Adapter → I2B → I2B↔Multi-Connector Adapter → State / Company / Person → Digital Economy Activities`

No existing layer, adapter, engine, authority, or invariant is renamed, removed, reordered, or bypassed by this proposal. The canonical freeze file must not be edited as part of this proposal.

## 2. Proposed additive structures

These remain documentation-level concepts; merging this proposal does not claim they are implemented, contract-tested, or production-enabled.

### A-01 — EXIM internal coordination specification

**Purpose:** specify how EXIM coordinates external institutional/system interfaces through explicit, versioned contracts.

- EXIM remains the core infrastructure's external-system boundary.
- External callers cannot access core internals directly.
- Each connector contract should define identity/context propagation, authorization, schema/versioning, idempotency, error mapping, audit evidence, timeout/retry, and recovery behavior.
- This proposal does not create a second ledger, escrow, witness chain, release authority, or settlement engine.

### A-02 — Digital Economy Port (DE Port)

**Purpose:** define the cross-border connection boundary at the top-level Digital Economy (DE) space.

- DE Port is a proposed international/cross-border connection concept at the DE level.
- It is distinct from EXIM Port: DE Port concerns cross-border ecosystem/economy connectivity; EXIM remains the core's external institutional/system interface.
- A cross-border connection must not bypass the canonical DE → DEE → G-3 → Core → EXIM → I2B route for core-authoritative operations.
- Funds, money, asset-rights, identity, compliance, or evidence exchange must be mediated by explicit contracts and retain the canonical infrastructure's authority boundaries.
- DE Port has no independent custody, ledger, escrow, release, or settlement authority.

### A-03 — Family Port

**Purpose:** propose a defined connection for person/family participation in Digital Economy activities.

- Family Port is a proposed connector/interface concept, not a new canonical infrastructure layer.
- It attaches through the existing PERSON and I2B connector boundaries.
- It cannot create a parallel identity authority, asset registry, ledger, escrow state, witness chain, or release path.
- Family-specific data access, consent, delegated authority, and privacy rules require a separate contract before implementation.

## 3. Approval and validation before implementation

For each proposal, record the precise boundary and owner; request/response contract and versioning; authority, identity, authorization, and audit requirements; failure/retry/idempotency/recovery behavior; compatibility and migration impact; contract tests proving no bypass of canonical boundaries; and explicit approval before implementation.

## 4. Exclusions

- SHUUD and SHIID remain separate applications; they are not folded into GerChain EAI.
- This document does not certify EAI as production-ready and does not declare a production final lock.
- No production code, database schema, migration, or existing frozen architecture document is changed by this proposal.

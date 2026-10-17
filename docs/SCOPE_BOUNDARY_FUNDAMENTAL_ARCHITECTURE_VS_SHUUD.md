# Scope Boundary — Canonical Fundamental Infrastructure vs SHUUD

**Status:** SCOPE CONTROL — AUTHORITATIVE FOR WORKSTREAM SEPARATION  
**Applies to:** `feat/ea21-transaction-aware-ledger` and subsequent fundamental-infrastructure readiness work  
**Canonical architecture reference:** `docs/DEE_ARCHITECTURE_FREEZE.md` (unchanged)  
**Purpose:** Prevent SHUUD product work from being conflated with the fundamental architecture and EAI production-readiness work.

## 1. Binding separation decision

**SHUUD is a separate product/workstream. SHUUD is not part of the fundamental architecture, is not a canonical infrastructure layer, and is not a prerequisite or acceptance criterion for the fundamental architecture or EAI.**

The fundamental-infrastructure workstream is limited to validating and locking:
- the frozen DE / DEE / G-3 / NEF + GerChain / EXIM / I2B architecture and its explicit adapters;
- EAI (Escrow as Infrastructure) as a governing infrastructure principle implemented through the existing G-3 foundation and canonical GerChain value-flow boundary;
- canonical durable truth, transaction correctness, witness, outbox, idempotency, recovery, security, observability, deployment, CI, and independent re-performance.

SHUUD work must not be inserted into this list as a layer, engine, authority, dependency, migration, release gate, or completion criterion.

## 2. Prohibited architectural coupling

No fundamental-infrastructure implementation or evidence may:
1. import, call, or require SHUUD modules to boot or validate the canonical runtime;
2. use SHUUD state, APIs, records, or business rules as authoritative infrastructure truth;
3. make fundamental architecture readiness depend on SHUUD MVP, product tests, product deployment, or product approval;
4. place SHUUD inside the frozen canonical architecture diagram or treat it as a sub-layer of NEF, G-3, GerChain, CORE, or EAI;
5. silently add SHUUD-specific code, configuration, schema, environment variables, or release gates to the fundamental runtime.

Any actual shared infrastructure contract must be explicit, versioned, adapter-mediated, and independently testable. Shared use does not merge the workstreams.

## 3. Workstream boundaries

### Workstream A — Fundamental architecture + EAI
Owns the frozen architecture, canonical value authority, escrow aggregate and lifecycle, transaction boundaries, witness/audit/outbox integrity, idempotency, reconciliation, fail-closed behavior, recovery, security, production deployment, CI, and independent evidence.

### Workstream B — SHUUD
Owns SHUUD product requirements, product workflows, product-specific interfaces, product tests, and product deployment. It proceeds separately and may consume only approved interfaces; it cannot redefine canonical truth or control the fundamental-infrastructure lock decision.

## 4. Acceptance and lock rules

The fundamental architecture + EAI may be locked only when its own required evidence is complete. SHUUD status is explicitly **NOT APPLICABLE** to this decision: SHUUD may be unfinished, paused, or independently released without changing the fundamental-infrastructure acceptance result.

Conversely, SHUUD passing its own tests does not prove that the fundamental architecture or EAI is production-ready.

## 5. Change control

This document is an additive scope-control decision. It does not rewrite or silently alter `docs/DEE_ARCHITECTURE_FREEZE.md`. Any future proposal to change the canonical architecture must follow the architecture-change approval process and must not use SHUUD product delivery as implicit authorization.

## 6. Required reporting format

Every fundamental-infrastructure progress report must state:
- **Scope:** Fundamental architecture + EAI only.
- **SHUUD:** Separate workstream; excluded from scope, dependencies, and acceptance criteria.
- **Evidence status:** Implemented / verified / unverified / open, distinguished precisely.
- **Lock status:** IN PROGRESS / NOT LOCKED until fresh, reproducible evidence supports a lock.

## Hard invariant

**SHUUD IS NOT PART OF THE FUNDAMENTAL ARCHITECTURE. FUNDAMENTAL ARCHITECTURE + EAI READINESS MUST BE VERIFIED AND LOCKED INDEPENDENTLY OF SHUUD.**

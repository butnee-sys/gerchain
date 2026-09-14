# GerChain Architecture Freeze

**Status:** Pre-freeze baseline
**Date:** 2026-09-14

This document defines the protected core architecture before SHUUD real E2E work.

## Canonical topology

```text
DE
 ↓ DE→DEE Adapter
DEE
 ↓ DEE→G-3 Adapter
G-3
 ↓ G-3→Core Adapter
NEF + GerChain Core
 ↓ Core→EXIM Adapter
EXIM Port
 ↓ EXIM→I2B Adapter
I2B Connection Gateway
 ├── Service Center
 └── Connectors
      ├── State
      ├── Company
      └── Person
```

## Protected ownership

- DEE owns governance, protection, trust, authorization policy, security, data governance, recovery policy and Self-Maintainer controls.
- G-3 owns condition, escrow and governance policy plus the Trust + Transparency + Performance release condition.
- NEF owns authoritative asset truth.
- GerChain owns authoritative operational value flow.
- EXIM is the controlled external boundary and is not an operational value-flow engine.
- I2B exposes approved infrastructure-to-business services and connectors; it does not duplicate core engines.

## Mandatory invariants

1. Every layer crossing uses an explicit adapter contract.
2. No direct layer-to-layer bypass is permitted.
3. Decision → Authorization → Release is mandatory.
4. Trust + Transparency + Performance must all PASS.
5. Evidence verification must PASS.
6. FAIL or UNKNOWN is fail-closed to DENY/HOLD.
7. Authoritative release uses PostgreSQL in production.
8. Value movement, witness, outbox creation and idempotency completion commit atomically.
9. Concurrent duplicate release produces exactly one authoritative value movement.
10. Recovery/replay must never create a second authoritative movement.
11. Self-Maintainer may observe, isolate, recover and verify but must not silently mutate authoritative financial or asset truth.
12. No second ledger, escrow, witness, settlement or asset-truth engine may be introduced in a boundary layer.

## Freeze rule

A change to this topology, ownership model or mandatory invariant requires an explicit architecture change proposal and corresponding tests. Product-specific applications, including SHUUD, must consume the frozen core rather than redesign it.

**Core is not declared frozen until the CORE_BASELINE completion criteria are green on the exact head commit.**

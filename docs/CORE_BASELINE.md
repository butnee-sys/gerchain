# GerChain Core Baseline

## Purpose

This is the completion gate for the **GerChain base structure**. SHUUD work must not become the acceptance criterion for the core.

> **Core first. SHUUD second.**

The core is complete only when the following layers are structurally present and connected without bypasses:

```text
DE
 ↓ DE→DEE Adapter
DEE
 ↓ DEE→G-3 Adapter
G-3
 ↓ G-3→Core Adapter
NEF + GerChain Core
 ↓ Core→EXIM Adapter
EXIM
 ↓ EXIM→I2B Adapter
I2B
```

## Ownership

- **DEE** — protection, governance, security, trust, authorization policy, recovery policy, Self-Maintainer.
- **G-3** — Condition Policy, Escrow Policy, Governance Policy, Trust + Transparency + Performance.
- **NEF** — authoritative asset truth: registration, identity, rights, valuation, evidence, verification, lifecycle, state.
- **GerChain** — operational value flow: account, ledger, money, hold, limit, collateral flow, escrow, witness, evidence, decision, authorization, release, transfer, clearing, settlement, payout, reconciliation, recovery, idempotency, consensus, audit, workflow and outbox.
- **EXIM** — controlled two-way boundary: validate, verify, authorize-check, route, regulate and audit external flow.
- **I2B** — infrastructure-to-business gateway with Service Center inside the Connection Gateway and State/Company/Person connectors outside the Service Center.

## Non-duplication rules

1. G-3 is not a second operational escrow engine.
2. DEE is not a second ledger, escrow, witness or settlement engine.
3. NEF owns asset truth; GerChain owns value flow.
4. GerChain collateral flow is not NEF collateral truth.
5. EXIM is a boundary, not a value-flow engine.
6. I2B Service Center dispatches services; it does not own authoritative financial or asset state.
7. Self-Maintainer may observe, decide, isolate, recover and verify; it must never silently mutate authoritative state.
8. External services must cross the approved adapters.

## Value-flow safety

The authoritative release invariant is:

```text
Decision = APPROVE
Authorization = AUTHORIZED
Trust = PASS
Transparency = PASS
Performance = PASS
Evidence = VERIFIED
        ↓
Atomic Release
        ↓
value movement + witness + outbox + idempotency completion
        ↓
ONE DATABASE COMMIT
```

Failure or UNKNOWN is fail-closed to DENY/HOLD.

## Completion criteria

The base structure is considered complete only after:

- architecture boundary tests pass;
- composition-root tests pass;
- DEE/G-3/NEF/GerChain ownership tests pass;
- EXIM and I2B boundary tests pass;
- production PostgreSQL runtime authority is explicit;
- atomic release, idempotency and concurrency tests pass against PostgreSQL;
- crash/replay and outbox recovery tests pass;
- Self-Maintainer safety tests pass;
- CI executes the core gate on the exact head commit;
- SHUUD tests are intentionally outside this core acceptance gate.

Only after all criteria are green may the repository be declared **CORE FROZEN** and the next workstream be SHUUD real E2E.

# CORE Freeze Record

**Decision:** CORE FROZEN — SHUUD real E2E may begin only after this gate remains green.
**Date:** 2026-09-14

## Verified controls

- canonical DE → DEE → G-3 → NEF + GerChain Core → EXIM → I2B topology: locked;
- ownership boundaries: locked;
- Layer → Adapter → Layer rule: enforced;
- G-3 is not a second operational escrow engine;
- NEF owns asset truth and does not own operational money/value-flow state;
- GerChain owns operational value flow;
- EXIM and I2B remain boundaries;
- PostgreSQL is the production release authority;
- atomic release, witness, outbox and idempotency invariants are covered by the CORE gate;
- concurrent duplicate release and crash/replay recovery are covered;
- Self-Maintainer safety is covered;
- capability reconciliation is governed by `MISSING = 0` and `DUPLICATE = 0`;
- SHUUD is downstream and is not used to satisfy CORE acceptance.

## Lock rule

After this record is committed, no CORE ownership, topology, authoritative-engine, release, settlement, ledger, witness, asset-truth, or adapter-boundary change may be made as part of SHUUD product work.

Any CORE architecture change requires a separate architecture-change proposal and a new CORE gate cycle.

The final main commit carrying this record must have the CORE gate green before SHUUD real E2E is treated as authorized to start.

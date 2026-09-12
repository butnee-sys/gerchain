# SHUUD Production-Readiness Technical Baseline

## Scope

This document records the technical baseline established after PR #17 and Issue #18 for the SHUUD 90-day sandbox.

## Verified lifecycle

`Incident → Evidence → SHIID APPROVE → Clearance → Escrow LOCKED → Release → Measurement Summary`

## Readiness gates

The PostgreSQL CI workflow is the authoritative readiness gate and runs, in order:

1. PostgreSQL concurrency suite
2. SHUUD PostgreSQL persistence suite
3. SHUUD measurement API E2E
4. SHUUD PostgreSQL process-restart E2E
5. SHUUD release CAS race test

A readiness run is acceptable only when all five stages pass in the same CI run and none of the readiness stages are skipped.

## Architecture invariants

- `WitnessChain` remains the authoritative witness engine.
- `EscrowEngine` remains the authoritative escrow state engine.
- SHUUD persistence is a durability/recovery layer and does not introduce a second witness chain or second escrow engine.
- Monetary semantics remain explicit: MNT is the currency and NEF is the settlement provider/infrastructure.
- Operational timing is derived from persisted SHUUD milestones, with clearance timing measured through the SHUUD clearance path.
- Economic measurement uses explicit sandbox inputs rather than hidden monetary assumptions.

## Sandbox role

This baseline is the technical foundation for the next phase: a controlled 90-day SHUUD sandbox focused on operational timing, evidence verification, rapid clearance, escrow settlement, and economic time-saved measurement.

# SHUUD — Independent Application Boundary

SHUUD is a standalone application/product built on the frozen NEF–GerChain platform.

## Ownership

- `apps/shuud/` owns SHUUD product behavior: incident intake, evidence, SHIID decisioning, clearance, application persistence, UI, economics, command layer and sandbox.
- NEF owns authoritative asset truth.
- GerChain CORE owns authoritative operational value flow, including ledger, money movement, escrow lifecycle, witness and PostgreSQL release authority.
- DEE/G-3/EXIM/I2B remain platform boundaries. SHUUD does not become a CORE engine.

## Allowed dependency direction

`SHUUD App → NEF–GerChain External Port / platform boundary → frozen platform`

SHUUD must not import GerChain CORE implementation modules such as `core.*`, `money.*`, `escrow.*`, `witness.*`, `verifier.*`, or `services.gerchain_runtime`.

The application may use the stable `nef_gerchain_port` contract and platform boundary adapters. Product decisions remain SHUUD-owned; authoritative settlement remains GerChain-owned.

## Repository structure

```text
apps/shuud/
├── application modules and APIs
├── integration/
│   ├── shuud_exim_flow.py
│   └── shuud_governed_flow.py
├── prototype/
├── sandbox/
└── ARCHITECTURE.md
```

The root `shuud/` package is only a temporary import facade for migration compatibility; it contains no product implementation. New code must use `apps.shuud` explicitly.

## Freeze rule

SHUUD work may evolve independently, but it may not modify CORE ownership, topology, authoritative engines, ledger/settlement truth, witness authority, or PostgreSQL release authority. A platform architecture change requires a separate CORE gate cycle.

# Canonical boundary implementation

This package is the implementation-side boundary map for `docs/DEE_ARCHITECTURE_FREEZE.md`.

## Locked architecture

```text
DE
 │
 ▼
DE ADAPTER
 │
 ▼
DEE
 │
 ▼
DEE ↔ G-3 ADAPTER
 │
 ▼
G-3
 │
 ▼
G-3 ↔ CORE ADAPTER
 │
 ▼
NEF + GERCHAIN CORE
 │
 ▼
CORE ↔ EXIM ADAPTER
 │
 ▼
EXIM PORT
 │
 ▼
EXIM ↔ I2B ADAPTER
 │
 ▼
I2B
 │
 ▼
I2B ↔ MULTI-CONNECTOR ADAPTER
 │
 ▼
MULTI-CONNECTOR
 ├── STATE
 ├── COMPANY
 └── PERSON
 │
 ▼
DIGITAL ECONOMY ACTIVITIES
```

Every shown layer-to-layer connection is an explicit adapter boundary. The
adapters carry contracts, authorization/context, and boundary translation;
they do not become new operational engines.

## Ownership rules

- DE is the top-level Digital Economy space.
- DEE owns ecosystem governance and protection.
- G-3 owns escrow conditions and governance policy.
- NEF owns asset registration, valuation and verification truth.
- GerChain owns operational asset value-flow truth.
- EXIM is the external boundary.
- I2B exposes infrastructure capabilities as business activities.
- Multi-Connector connects State, Company and Person actors.
- Applications consume these boundaries rather than bypassing them.

## Adapter rules

- No layer may directly bypass its defined adapter boundary.
- DE must enter DEE through the DE Adapter.
- DEE and G-3 communicate through their explicit adapter.
- G-3 reaches NEF + GerChain through the G-3/Core Adapter.
- Core reaches EXIM only through the Core/EXIM Adapter.
- EXIM reaches I2B only through the EXIM/I2B Adapter.
- I2B reaches actors only through the I2B/Multi-Connector Adapter.
- The existing `nef_gerchain_port` remains compatible with this boundary model; it
  is not an excuse to bypass the canonical adapters.

## Explicit non-goals

This package does **not** add another ledger, witness chain, escrow engine,
decision engine, authorization engine, release engine, settlement engine,
or authoritative asset registry.

Those remain in the existing infrastructure and are reached only through
governed contracts.

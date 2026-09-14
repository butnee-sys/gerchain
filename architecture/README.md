# Canonical boundary implementation

This package is the implementation-side boundary map for `docs/DEE_ARCHITECTURE_FREEZE.md`.

```text
DE
 -> DEE
 -> G-3
 -> CoreAdapter
 -> EXIMPort
 -> I2BGateway
 -> MultiConnectorAdapter
 -> State / Company / Person Connector
 -> Digital Economy Activity
```

## Ownership rules

- DEE owns ecosystem governance and protection.
- G-3 owns escrow conditions and governance policy.
- NEF owns asset registration, valuation and verification truth.
- GerChain owns operational asset value-flow truth.
- EXIM is the external boundary.
- I2B exposes infrastructure capabilities as business activities.
- Connectors represent State, Company and Person actors.
- Applications must consume these boundaries rather than bypassing them.

## Explicit non-goals

This package does **not** add another ledger, witness chain, escrow engine,
decision engine, authorization engine, release engine, settlement engine,
or authoritative asset registry.

Those remain in the existing infrastructure and are reached only through
governed contracts.

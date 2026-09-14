# Canonical Composition Root

## Purpose

This document freezes the executable boundary composition for the digital economy flow.

```text
DE
  -> DEToDEE Adapter
DEE
  -> DEEToG3 Adapter
G-3
  -> G3ToCore Adapter
NEF + GerChain Core
  -> CoreToEXIM Adapter
EXIM
  -> EXIMToI2B Adapter
I2B
```

The implementation follows **Layer -> Adapter -> Layer** at every hop.

## Rules

1. The composition root wires boundaries; it does not create operational engines.
2. A rejected layer response stops downstream flow.
3. An invalid `BoundaryRequest` or `BoundaryResponse` fails closed.
4. Ledger, Money, Escrow, Witness, Authorization, Release, Settlement and NEF asset truth remain owned by their existing layers.
5. No layer may bypass its explicit adapter to call another layer.
6. The composition root is the single wiring point for the canonical path.

## Scope

This closes the architectural composition gap for the DE -> DEE -> G-3 -> Core -> EXIM -> I2B path. PostgreSQL authority, concurrency/recovery proof and executable Self-Maintainer remain later gates.

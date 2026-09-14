# GATE-02 Capability Classification Contract

GATE-02 is a reconciliation gate, not an engine-building gate.

For every conceptual GerChain capability, exactly one authoritative owner must
be identified. If the capability is not an engine, its non-engine category must
be explicit.

## Classification

- AUTHORITATIVE — executable owner + invariant tests.
- COMPOSITE — composed from existing authoritative capabilities.
- BOUNDARY — adapter, port, gateway, or translation only.
- POLICY — decision/constraint only.
- STRUCTURAL — schema, DTO, type, hash, or documentation only.
- MISSING — required behavior has no authoritative owner.
- DUPLICATE — multiple components claim the same authority.

## Reconciliation invariant

The current GATE-02 capability reconciliation must finish with:

- `MISSING = 0`
- `DUPLICATE = 0`

These are gate invariants, not a claim that every conceptual capability is an
independent engine.

## Freeze rule

`MISSING` and `DUPLICATE` block CORE freeze.

A new operational engine is prohibited merely to make a conceptual capability
appear complete. First map it to an existing authority. Only a documented
architecture change may create a new authority.

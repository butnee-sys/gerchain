# GATE-06 — DEE Self-Maintainer Contract

The Self-Maintainer is part of the DEE protection fabric. It is not an operational value-flow engine.

## Responsibilities

- Health observation
- Integrity verification
- Dependency checks
- Lifecycle checks
- Version observation
- Isolation decision
- Recovery decision

## Safety invariant

```text
Self-Maintainer
      ↓
observe → decide → isolate/recover → verify

NEVER
      ↓
mutate authoritative ledger / escrow / asset truth
```

Unknown or unverified integrity is fail-closed to `ISOLATE`.

A healthy component produces `NONE`. A failed component requests `RECOVER`.

The component returns maintenance decisions; execution of recovery remains outside authoritative financial and asset state mutation.

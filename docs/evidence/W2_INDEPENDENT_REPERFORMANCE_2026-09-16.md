# W2 Independent Re-performance Record — 2026-09-16

## Verdict

**PASS — independent semantic re-performance completed.**

This record is independent semantic evidence only. It does not by itself declare W2 final GREEN, CORE GREEN, or CORE LOCK.

## Independence

The execution was performed in a separate Linux runtime outside the GerChain repository working tree and did not invoke the production release implementation, production persistence layer, or production economic-state fingerprint implementation.

Independent implementation artifact:

`tests/independent/w2_reperformance.py`

Independent implementation SHA-256:

`b57478d5b8a9a7d205f4d325d5b712a0807725ec157f87c0575213df8d7c46b4`

## Environment

- Runtime: Python 3.13.5
- OS/kernel: Linux x86_64, kernel 6.18.44
- Execution timestamp: `2026-09-16T16:02:45Z`

## C2 — Shared liquidity

Frozen input:

```text
capacity = 2,000,000
requests = (1,500,000, 1,500,000)
```

Independent result:

```text
committed = (1,500,000, 0)
committed_total = 1,500,000
over_allocated = false
conservation_holds = true
```

Therefore:

```text
committed_total <= capacity
```

and the shared-liquidity conservation invariant holds.

## C6 — Stale decision

Frozen decision state:

```text
source_account = A
source_balance = 2,000,000
escrow_id = E
escrow_state = LOCKED
escrow_amount = 1,000,000
requested_amount = 1,000,000
```

Current state changes only:

```text
source_balance = 500,000
```

Independent result:

```text
stale_decision_accepted = false
```

Thus the independent semantic implementation rejects execution when the relevant economic state differs.

## Agreement

Production-side W2 CI previously established the same declared C2 aggregate and C6 stale-state behavior. The independent implementation reproduced those economic invariants without importing production code.

Agreement is evaluated at the invariant/semantic level, not by requiring identical internal implementation or winner identity for concurrent requests.

## Evidence limitations

This execution is an independent semantic re-performance, not an independent PostgreSQL deployment. It therefore validates the W2 semantic claims C2/C6 but does not independently reproduce database locking, transaction isolation, row-lock behavior, or PostgreSQL crash/recovery mechanics.

Those remain covered by the production PostgreSQL integration evidence and must not be conflated with this independent record.

## Closure recommendation

With this record attached to the W2 evidence manifest:

```text
Independent semantic reproduction = PASS
W2 evidence completeness = substantially advanced
W2 final scientific closure = requires final evidence reconciliation
```

No automatic promotion to CORE GREEN or CORE LOCK is permitted.

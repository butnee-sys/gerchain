# CORE W2 — Evidence Manifest

## Status

**W2 technical/scientific closure: GREEN on commit `d8d71750ed2dc17f43f460ff9e2ab809a9c1b6b6`.**

This manifest closes W2 only. It does **not** declare final CORE GREEN or CORE LOCK.

## Scope

CORE only. SHUUD is explicitly excluded from W2 assurance and cannot be used to close any W2 control.

## Current execution evidence

| Field | Value |
|---|---|
| Gate | W2 — PostgreSQL concurrency and stale-decision validity |
| Execution commit | `d8d71750ed2dc17f43f460ff9e2ab809a9c1b6b6` |
| core-gates run | `35119696983` — SUCCESS |
| PostgreSQL Concurrency run | `35119696806` — SUCCESS |
| CORE Operating Reconciliation run | `35119696769` — SUCCESS |
| CodeQL Advanced run | `35119696782` — SUCCESS |
| Independent PostgreSQL re-performance | included in `core-gates` — PASS |

The execution commit added the independent PostgreSQL re-performance step to `core-gates` and CI completed successfully.

## W2 evidence chain

`Contract -> Production implementation -> PostgreSQL adversarial tests -> Independent oracle -> Oracle agreement -> Deterministic reproduction -> Independent semantic re-performance -> Independent PostgreSQL re-performance -> Evidence reconciliation -> GREEN`

## C2 — Shared liquidity

Claim: distinct concurrent economic operations sharing one canonical liquidity capacity cannot commit value beyond that capacity.

Frozen vector:

- capacity = `2,000,000`
- request A = `1,500,000`
- request B = `1,500,000`
- distinct transaction/escrow identities

Required invariants:

- `sum(CommittedConsumption) <= Capacity`
- `OverAllocation = 0`
- `LostUpdate = 0`
- exactly one 1.5M release commits for the 2M capacity

Production PostgreSQL integration and independent PostgreSQL re-performance both enforce the shared-capacity serialization semantics. The independent semantic oracle independently produces the aggregate `(1,500,000, 0)`.

**C2 verdict: GREEN.**

## C6 — Stale decision

Claim: a decision bound to a relevant economic state cannot execute after that relevant state changes without a new valid decision/state transition.

Frozen decision state:

- source balance = `2,000,000`
- escrow state = `LOCKED`
- escrow amount = `1,000,000`
- requested amount = `1,000,000`

Relevant state mutation:

- source balance changes to `500,000`

Required invariants:

- `StaleDecisionExecution = 0`
- `EconomicStateMismatch = 0`
- no value movement on stale rejection
- no witness creation on stale rejection
- no release operation committed on stale rejection

Production PostgreSQL guard and independent PostgreSQL re-performance reject the stale state before economic mutation. The independent semantic implementation also rejects the changed state.

**C6 verdict: GREEN.**

## Independent evidence

### Semantic re-performance

- implementation: `tests/independent/w2_reperformance.py`
- implementation SHA-256: `b57478d5b8a9a7d205f4d325d5b712a0807725ec157f87c0575213df8d7c46b4`
- runtime: Python 3.13.5 / Linux x86_64
- result: PASS

### PostgreSQL re-performance

- implementation: `tests/independent/w2_postgres_reperformance.py`
- separate implementation boundary: no GerChain production persistence/release/fingerprint imports
- execution: CI `core-gates` run `35119696983`
- result: PASS
- C2: one of two concurrent 1.5M consumers commits; total committed = 1.5M <= 2M
- C6: changed PostgreSQL state causes stale decision rejection before mutation

The PostgreSQL re-performance is independent at the implementation/test-path level. It is not an external auditor attestation.

## Evidence reconciliation

All W2 evidence is now tied to the execution commit `d8d71750ed2dc17f43f460ff9e2ab809a9c1b6b6` for the current technical run. Earlier commit evidence remains historical baseline and is not used as current GREEN evidence.

The following evidence classes agree on the declared W2 invariants:

1. W2 contract
2. production PostgreSQL integration tests
3. independent semantic oracle
4. deterministic reproduction
5. independent semantic re-performance
6. independent PostgreSQL re-performance
7. current CI execution

No SHUUD code, route, product logic, sandbox result, or dependency is used to close W2.

## Exit criteria

- C2 invariant contract defined: PASS
- C2 production PostgreSQL test: PASS
- C2 independent oracle: PASS
- C2 deterministic reproduction: PASS
- C2 independent semantic re-performance: PASS
- C2 independent PostgreSQL re-performance: PASS
- C6 invariant contract defined: PASS
- C6 production PostgreSQL test: PASS
- C6 independent oracle: PASS
- C6 deterministic reproduction: PASS
- C6 independent semantic re-performance: PASS
- C6 independent PostgreSQL re-performance: PASS
- evidence reconciled to current execution commit: PASS
- critical unresolved W2 contradiction: NONE IDENTIFIED

## W2 final determination

**GREEN**

Meaning of GREEN here is bounded and evidence-based:

> Within the declared W2 domain and frozen test vectors, the tested shared-liquidity concurrency and stale-decision validity invariants have current, reproducible, independently re-performed evidence.

GREEN does not mean universal economic stability, final CORE GREEN, CORE LOCK, or SHUUD readiness.

## Non-claims

This record does not claim:

- universal economic stability;
- final CORE GREEN;
- CORE LOCK;
- SHUUD readiness;
- validity outside the declared W2 domain;
- external auditor attestation.

## State transition

`W2 OPEN -> REVALIDATED -> INDEPENDENTLY RE-PERFORMED -> EVIDENCE RECONCILED -> GREEN`

Next gate: **W3 — Schema Concurrency**.

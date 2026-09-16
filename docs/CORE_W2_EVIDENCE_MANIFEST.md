# CORE W2 — Evidence Manifest

## Status

**Technical CI status: GREEN on commit `d5211818aff0bac86d1f2ada7cd9868fff089dba`.**

This manifest records the current W2 evidence boundary. It does **not** declare final CORE GREEN or CORE LOCK.

## Scope

CORE only. SHUUD is explicitly excluded from W2 assurance.

## Current execution evidence

| Field | Value |
|---|---|
| Gate | W2 — PostgreSQL concurrency and stale-decision validity |
| Commit | `d5211818aff0bac86d1f2ada7cd9868fff089dba` |
| core-gates run | `35118708690` |
| PostgreSQL Concurrency run | `35118708699` |
| CORE Operating Reconciliation run | `35118708662` |
| CodeQL run | `35118708694` |
| core-gates conclusion | SUCCESS |
| PostgreSQL Concurrency conclusion | SUCCESS |
| Operating Reconciliation conclusion | SUCCESS |
| CodeQL conclusion | SUCCESS |

## Executed W2 test set

The `core-gates` job executed:

- `tests/test_economic_state_fingerprint.py`
- `tests/test_postgres_w2_shared_liquidity.py`
- `tests/test_postgres_w2_stale_decision.py`
- `tests/test_w2_independent_oracle.py`
- `tests/test_w2_oracle_agreement.py`
- `tests/test_w2_independent_reproduction.py`

The W2 step completed successfully in the current `core-gates` run.

## C2 evidence

Claim: distinct concurrent economic operations sharing one canonical liquidity capacity cannot commit value beyond that capacity.

Test vector:

- capacity = `2,000,000`
- request A = `1,500,000`
- request B = `1,500,000`
- distinct transaction/escrow identities

Required invariants:

- `sum(CommittedConsumption) <= Capacity`
- `OverAllocation = 0`
- `LostUpdate = 0`
- exactly one 1.5M release commits for the 2M source capacity

Independent oracle expectation for the ordered semantic vector:

`(1,500,000, 0)`

The PostgreSQL implementation may determine which concurrent request wins; the economic aggregate must remain within capacity.

## C6 evidence

Claim: a decision bound to a relevant economic state cannot execute after that relevant state changes without a new valid decision/state transition.

The decision identity is based on a canonical relevant-state fingerprint. The PostgreSQL guard locks the relevant source and escrow rows, computes the current fingerprint, and rejects a mismatch before economic mutation.

Required invariants:

- `StaleDecisionExecution = 0`
- `EconomicStateMismatch = 0`
- no value movement on stale rejection
- no witness creation on stale rejection
- no release operation committed on stale rejection

Independent semantic oracle uses direct state equality and does not import the production persistence or release implementation.

## Deterministic reproduction

The deterministic reproduction suite independently replays the C2 and C6 semantic vectors. It is explicitly **not** treated as a second deployment or external independent audit.

Therefore:

`DeterministicReproduction != IndependentRe-performance`

## Evidence classification

Current evidence supports:

`Contract + Automated PostgreSQL Test + Independent Semantic Oracle + Deterministic Reproduction + CI execution`

It does not yet support an external independent re-performance claim.

## Remaining W2 closure

1. Preserve this manifest against the exact execution commit.
2. Obtain a genuinely independent re-performance using a separate execution environment and/or implementation.
3. Compare the independent result to the current evidence without allowing the production implementation to define the oracle.
4. Record the independent run identity and result.
5. Only then issue the W2 final GREEN determination.

## Non-claims

This manifest does not claim:

- universal economic stability;
- final CORE GREEN;
- CORE LOCK;
- SHUUD readiness;
- validity outside the declared W2 domain;
- external auditor attestation.

## Closure rule

`NoEvidence -> NoClaim`

`OldEvidence != CurrentGREEN`

`TechnicalPASS != ScientificFinalClosure`

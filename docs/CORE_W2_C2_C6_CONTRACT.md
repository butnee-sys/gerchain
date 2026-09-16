# CORE W2 — C2/C6 Contract

## Scope

CORE only. SHUUD is out of scope and must not be used to satisfy any W2 gate.

## C2 — Shared Liquidity Concurrency

### Claim
Distinct concurrent economic operations sharing one canonical liquidity capacity must not over-allocate that capacity or lose committed state.

### Canonical state

`LiquidityState = (LiquidityID, Capacity, Reserved, Consumed, Version, Status)`

### Invariants

- `I-C2.1: sum(CommittedConsumption) <= Capacity`
- `I-C2.2: OverAllocation = 0`
- `I-C2.3: LostUpdate = 0`
- `I-C2.4: Canonical liquidity version/state is serialized for conflicting writes`
- `I-C2.5: Retry of the same economic operation is idempotent`
- `I-C2.6: A distinct operation is not incorrectly classified as a replay`

### Falsification

C2 is RED if any adversarial concurrent schedule produces over-allocation, lost update, duplicated committed consumption, or an accepted operation whose committed state exceeds canonical capacity.

### Required adversarial shape

At least two distinct transaction identities must concurrently consume the same canonical liquidity resource. Same-idempotency-key replay tests alone are insufficient.

---

## C6 — Stale Decision Validity

### Claim
A decision approved against a relevant economic state must not execute after that relevant state has changed unless a new valid decision is produced.

### Decision object

`Decision = (DecisionID, Action, Scope, StateFingerprint, StateVersion, EffectiveTime, Authority, Evidence, Status)`

### Relevant state identity

`StateFingerprint = H(CanonicalRelevantEconomicState)`

The fingerprint covers only state semantically relevant to the decision; it is not an arbitrary hash of the whole database.

### Execution rule

`Execute(D) iff GovernancePASS AND CurrentStateFingerprint == D.StateFingerprint AND DecisionEffective AND DecisionAuthorized`

Otherwise execution must terminate as `HOLD` or `REJECT_STALE` without economic mutation.

### Invariants

- `I-C6.1: StaleDecisionExecution = 0`
- `I-C6.2: EconomicStateMismatch = 0`
- `I-C6.3: Decision state fingerprint is captured at decision time`
- `I-C6.4: Execution compares against canonical current relevant state`
- `I-C6.5: State mismatch cannot silently downgrade to a normal release`
- `I-C6.6: A new state requires a new decision or an explicitly valid state transition`

### Falsification

C6 is RED if a decision with a mismatching relevant-state fingerprint can cause value movement, ownership/right change, obligation change, liquidity commitment, settlement, or finality.

---

## Shared rule

`RequestIdentity != EconomicStateIdentity`

`OperationFingerprint != DecisionStateFingerprint`

`GREEN(C2) && GREEN(C6)` requires independent evidence for both; one test cannot substitute for the other.

## Closure path

`Contract -> Implementation -> Adversarial PostgreSQL Test -> Independent Oracle -> Evidence -> Independent Reproduction`

Historical evidence does not close current W2.

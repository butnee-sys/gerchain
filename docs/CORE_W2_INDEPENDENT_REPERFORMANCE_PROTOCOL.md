# CORE W2 — Independent Re-performance Protocol

## Purpose

Provide a reproducible procedure for a genuinely independent W2 semantic re-performance after the production implementation and deterministic in-repository oracle have passed CI.

## Independence boundary

The independent executor MUST NOT import or call:

- `persistence.atomic_release`
- `persistence.decision_bound_release`
- `core.economic_state`
- `core.idempotency`
- production release services
- production operation outcomes

The independent implementation may read only the W2 contract and declared input vectors.

## Required separation

There are three distinct layers:

1. **Production implementation** — GerChain PostgreSQL execution.
2. **In-repository semantic oracle** — `tests/oracles/w2_independent_oracle.py`.
3. **Independent re-performance implementation** — `tests/independent/w2_reperformance.py`.

Layer 3 is not allowed to derive its expected result from layers 1 or 2.

## Frozen input vector

### C2

```text
capacity = 2,000,000
requests = (1,500,000, 1,500,000)
```

Expected semantic properties:

```text
committed_total = 1,500,000
committed_total <= capacity
no over-allocation
```

The identity of the winning request is not a scientific requirement; aggregate conservation is.

### C6

Decision state:

```text
source_account = A
source_balance = 2,000,000
escrow_id = E
escrow_state = LOCKED
escrow_amount = 1,000,000
requested_amount = 1,000,000
```

Current state is identical except:

```text
source_balance = 500,000
```

Required result:

```text
decision accepted = false
```

No economic mutation is permitted for the stale decision.

## Execution

The independent executor should run the independent implementation from a separately provisioned Python environment or separate machine/process boundary, record:

- environment identity
- Python/runtime version
- source commit or package hash
- input vector hash
- implementation hash
- execution timestamp
- output
- invariant verdict
- execution log hash

The executor should run the implementation directly rather than through the production test suite.

Example:

```bash
python tests/independent/w2_reperformance.py
```

## Evidence record

Independent evidence MUST identify the exact implementation artifact used. A successful CI run of the production branch is not itself independent evidence.

Minimum record:

```text
IndependentRunID
EnvironmentFingerprint
ImplementationHash
InputHash
ExecutionTimestamp
C2Result
C6Result
InvariantVerdict
LogHash
Operator/Executor
```

## Agreement rule

For C2:

```text
IndependentCommittedTotal == ProductionCommittedTotal == 1,500,000
IndependentOverAllocation == false
```

For C6:

```text
IndependentDecisionAccepted == false
ProductionDecisionAccepted == false
```

Invariant disagreement is a hard failure. Formatting or winner-identity differences are not failures when the declared economic invariants agree.

## Closure rule

Independent agreement is necessary but not sufficient for W2 GREEN. W2 final closure also requires the evidence manifest to reference the independent execution and all critical W2 evidence to be tied to the same declared scope.

Therefore:

```text
IndependentPASS
  + EvidenceComplete
  + ScopeConsistent
  + NoCriticalMismatch
  -> W2 GREEN candidate
```

No W2 result may be promoted automatically to CORE GREEN or CORE LOCK.

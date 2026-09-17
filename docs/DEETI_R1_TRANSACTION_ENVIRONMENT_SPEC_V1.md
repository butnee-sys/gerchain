# DEETI R1 Transaction Environment Specification v1

**Status:** PROVISIONAL — NOT FROZEN
**Scientific status:** R0

## 1. Selection target

The primary experimental environment is provisionally defined as a **generic digital escrow/payment transaction** rather than a SHUUD/SHIID-specific road incident transaction.

Reason: the generic escrow/payment environment gives the cleanest separation between the foundational capability under test and application-specific factors.

## 2. Experimental unit

One transaction episode is one independent economic exchange between a provider and counterparty with:

- a defined economic object or service;
- a declared transaction value;
- a predefined completion condition;
- a settlement event;
- auditable evidence;
- a terminal state.

## 3. Treatment and control

### Control

The same transaction process operates without the full Escrow Trinity capability bundle.

### Treatment

The same process operates with the pre-specified ET capability:

`Trust + Transparency + Verified Fulfilment`.

No other material transaction rule should differ between arms.

## 4. Required variation

The environment is eligible only if ET capability can be assigned or credibly varied independently of the underlying economic task.

Minimum requirement:

```text
Treatment assignment
        ↓
ET capability exposure
        ↓
transaction lifecycle
        ↓
O1 outcome
```

ETI must not be calculated from O1.

## 5. Real consequence requirement

The primary experiment must involve either real economic value or a consequential transaction where completion/failure has a meaningful operational consequence.

Pure synthetic data are not eligible for confirmatory inference.

## 6. Primary outcome

`O1 = completed initiated transactions / initiated transactions`.

Completion is independently adjudicated under the frozen O1 coding protocol.

## 7. Required evidence

Each eligible transaction should permit reconstruction of:

- treatment assignment;
- initiation;
- Trust indicators;
- Transparency indicators;
- Verified Fulfilment indicators;
- condition verification;
- escrow lock/release/refund;
- completion/failure/dispute;
- timestamps;
- provenance and audit trail.

## 8. Exclusion rules

Reject as primary evidence when:

- ETI is derived from O1;
- treatment assignment is outcome-dependent;
- outcome coding is controlled by the treatment implementer without independent verification;
- provenance cannot be reconstructed;
- negative outcomes are systematically unavailable;
- control and treatment differ in the underlying economic task;
- only simulated/synthetic outcomes exist.

## 9. Relationship to SHUUD/SHIID

SHUUD/SHIID remains a later application-domain replication candidate. It is not the foundational experiment because road incidents introduce additional variables including insurance rules, operator behavior, AI confirmation, traffic conditions, and user behavior.

## 10. Freeze gate

The transaction environment is not R1-frozen until all are specified:

`ConcreteDomain ∧ Population ∧ TransactionValueRange ∧ TreatmentImplementation ∧ ControlImplementation ∧ AllocationRule ∧ RealConsequence ∧ IndependentO1Coding ∧ Provenance ∧ δ ∧ α ∧ Power ∧ SampleSize ∧ MissingnessRules`.

Current state: **PROVISIONAL / R0**.

# DEETI R1 Real Source Gate v1

**Status:** R1 preparation
**Scientific status:** R0
**Date:** 2026-09-17

## Gate objective

A real empirical source may be frozen as the primary source only when it satisfies the complete evidence-chain requirements.

## Mandatory predicate

```text
SourceAccessible
∧ ObservationUnitDefined
∧ O1Reconstructable
∧ ETIReconstructable
∧ ETI_O1_Separated
∧ TemporalOrderingValid
∧ ComparisonFeasible
∧ ProvenanceComplete
∧ NegativeEvidenceAvailable
∧ DefinitionStabilityVerified
∧ ReproducibilityFeasible
```

## Additional requirement for causal language

If the intended interpretation is causal, add:

```text
CredibleCounterfactual
∧ TreatmentAssignmentIdentified
∧ ConfoundingAddressed
∧ TemporalPrecedenceEstablished
```

Otherwise the analysis remains associational.

## Freeze rule

The source is not frozen merely because it appears promising. The source is frozen only after this predicate is documented and signed/versioned in the research branch.

## Current status

```text
PRIMARY_SOURCE = NOT_FROZEN
R1 = INCOMPLETE
R0 = ACTIVE
```

No empirical support for H1 is claimed at this gate.

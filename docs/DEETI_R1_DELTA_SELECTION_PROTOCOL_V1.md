# DEETI R1 Practical-Effect Delta Selection Protocol v1

**Status:** PROVISIONAL — NOT FROZEN  
**Scientific stage:** R0 / R1 preparation

## 1. Purpose

Define how the practical-effect threshold `δ` for the primary outcome O1 will be selected without inspecting confirmatory treatment outcomes.

## 2. Primary outcome

`O1 = completed initiated transaction episodes / initiated transaction episodes`

The practical-effect threshold is an absolute difference in O1 between ET treatment and control:

`δ = O1_ET - O1_Control`

## 3. What δ means

`δ` is not a statistical significance threshold. It is the smallest improvement that would be considered materially useful in the chosen transaction environment.

The threshold must therefore be justified by consequences external to the observed confirmatory result.

## 4. Evidence hierarchy for δ justification

Use, in order where available:

1. Direct operational cost of an incomplete transaction.
2. Direct settlement delay or dispute cost.
3. Expected economic loss avoided by successful completion.
4. Decision-maker-defined minimum improvement required to change an operational decision.
5. Prior independent empirical evidence from comparable transaction environments.
6. Published domain benchmarks.

If none provide a defensible threshold, δ remains **UNFROZEN** and no confirmatory sample-size claim is permitted.

## 5. Three-part justification test

A proposed δ must satisfy all three:

`EconomicMeaning ∧ OperationalMeaning ∧ PreOutcomeSpecification`

### EconomicMeaning

The improvement must correspond to a measurable reduction in loss, delay, dispute cost, capital lock-up, or other consequential economic burden.

### OperationalMeaning

The improvement must be large enough to change a real process decision, not merely produce a numerically detectable difference.

### PreOutcomeSpecification

The threshold must be documented before the confirmatory O1 results are inspected.

## 6. Candidate planning values

For planning only, candidate absolute effects may include:

- `δ = 0.02`
- `δ = 0.03`
- `δ = 0.05`

These are **illustrative scenarios, not selected thresholds**.

## 7. What is prohibited

The following are not acceptable justifications for δ:

- choosing the smallest effect that achieves p < 0.05;
- choosing δ after inspecting treatment/control outcomes;
- choosing δ solely because it produces a convenient sample size;
- choosing δ from a synthetic workload result;
- choosing δ from the highest-performing prior study;
- choosing δ without identifying its economic or operational consequence.

## 8. Current source implications

The 2004 settlement-escrow experiment is useful design precedent because it experimentally examined settlement rate, outcome quality, uncertainty, and escrow. It reported higher settlement rates with escrow under asymmetric information and lower litigation costs, but its setting does not provide a direct DEETI-specific practical-effect threshold. Therefore it cannot by itself freeze δ. citeturn0search0

The 2008 trust-game escrow experiment also provides experimental precedent for linking escrow precommitment to efficient outcomes, but it does not establish a DEETI-specific δ. citeturn0search3

## 9. Freeze gate

`DeltaFrozen = EconomicMeaning ∧ OperationalMeaning ∧ PreOutcomeSpecification ∧ SourceTraceability`

Until `DeltaFrozen = TRUE`:

- power analysis remains scenario planning;
- sample size remains provisional;
- R1 is not GREEN;
- no confirmatory result may be interpreted against an unfrozen practical threshold.

## 10. Next action

Select one concrete generic escrow transaction environment and document its measurable cost of failure, delay, dispute, and successful completion. Use those consequences to propose a defensible δ before collecting or inspecting confirmatory outcomes.

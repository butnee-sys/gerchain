# DEETI R1 — Economic Consequence Measurement Protocol v1

**Status:** PROVISIONAL — NOT FROZEN  
**Research stage:** R0 / R1 preparation  
**Branch:** `research/deeti-foundational-capability-v1`

## 1. Purpose

This protocol defines how the economic and operational consequence of an unsuccessful or delayed transaction will be measured before selecting the practical-effect threshold `δ` for the DEETI foundational-capability test.

The protocol does **not** select a numerical `δ` by itself. It establishes the evidence required to justify one before confirmatory outcome inspection.

## 2. Primary outcome remains fixed

The primary outcome is:

`O1 = completed governed transaction episodes / initiated governed transaction episodes`

The consequence protocol must therefore explain why an improvement in O1 is economically meaningful in the selected transaction environment.

## 3. Consequence dimensions

For each eligible transaction environment, measure consequences in four separate dimensions:

1. **Direct loss (L1)** — value or cost directly lost when an initiated transaction fails or cannot be completed.
2. **Delay cost (L2)** — measurable cost caused by additional settlement time, including time-sensitive service interruption or capital lock-up where objectively measurable.
3. **Dispute cost (L3)** — direct resource cost attributable to dispute handling, verification, recovery, refund, or escalation.
4. **Opportunity cost (L4)** — independently measurable economic activity forgone because the transaction remains unresolved.

These dimensions must not be combined unless a defensible common monetary unit and conversion rule are established before confirmatory outcome inspection.

## 4. Required evidence

A candidate consequence measure is admissible only if its source can be traced to one of the following:

- transaction or settlement records;
- independently auditable operational records;
- documented service-level or contractual cost schedules;
- independently collected experimental records;
- published empirical evidence from a comparable transaction environment.

Pure expert opinion may be used only as supporting evidence, not as sole justification for `δ`.

## 5. Per-transaction consequence record

Minimum fields:

```text
transaction_id
transaction_value
initiated_at
completed_at
terminal_state
failure_flag
dispute_flag
settlement_delay
verification_delay
direct_loss
settlement_cost
dispute_cost
opportunity_cost
consequence_source
source_version
measurement_method
measurement_uncertainty
```

All monetary values must record currency, price basis, and observation period.

## 6. Counterfactual requirement

The protocol must distinguish:

`Observed consequence` from `Counterfactual consequence avoided by successful completion`.

A consequence cannot be attributed to DEETI merely because it occurred after treatment exposure. Attribution requires the pre-specified comparison design from the experimental protocol.

For randomized treatment/control data:

`ATE_consequence = E(C | ET) - E(C | Control)`

where `C` is a pre-specified consequence measure.

For `δ`, however, the preferred justification is not the observed treatment effect. `δ` must represent the **minimum decision-relevant improvement** that has independent economic meaning.

## 7. Translating consequence into practical δ

Candidate `δ` must satisfy all three conditions:

`EconomicMeaning ∧ OperationalMeaning ∧ PreOutcomeSpecification`

A defensible procedure is:

1. identify the minimum consequence caused by one failed transaction episode;
2. estimate the expected annual/monthly number of eligible transaction episodes;
3. determine the minimum aggregate improvement that would materially change the economic or operational decision;
4. convert that decision threshold into a transaction-level O1 improvement;
5. freeze `δ` before inspecting confirmatory O1 outcomes.

Illustrative only:

`δ = minimum decision-relevant reduction in unsuccessful transaction episodes`

No value such as 0.02, 0.03, or 0.05 is selected by this document.

## 8. Exclusion rules

The following cannot justify `δ`:

- statistical significance obtained from the confirmatory experiment;
- the observed DEETI treatment effect;
- the largest effect among candidate samples;
- a value selected because it produces a convenient sample size;
- synthetic workload cost with no real-world consequence mapping;
- post-treatment economic outcomes;
- an unsupported expert estimate;
- a consequence measure that is itself constructed from O1.

## 9. Falsification relevance

The foundational claim must remain falsifiable. If ET increases O1 by less than the independently justified practical threshold `δ`, the result is **not practically supportive** even if statistically significant.

Conversely, an improvement exceeding `δ` does not establish the foundational claim by itself; causal validity, ETI measurement validity, independence, robustness, and replication remain necessary.

## 10. Evidence precedent

Existing experimental literature shows that escrow effects can be context-dependent. Babcock and Landeo (2004) found significantly higher settlement rates with a settlement escrow under asymmetric information, while reporting no escrow effect under the certainty condition. This supports using context-specific consequences and explicit falsification rather than assuming a universal escrow effect. citeturn0search0turn0search4

The 1995 Gertner–Miller model likewise frames escrow as a mechanism that can reduce delay by reducing inference costs under asymmetric information. citeturn0search7

These sources are **design precedents, not evidence that DEETI is validated**.

## 11. Freeze gate

`ConsequenceFreeze =`

`ConsequenceDimensionsDefined`

`∧ SourceHierarchyDefined`

`∧ MonetaryBasisDefined`

`∧ CounterfactualRuleDefined`

`∧ DecisionRelevanceDefined`

`∧ OutcomeInspectionBlocked`

`∧ ProvenanceTraceable`

Only after this gate is satisfied may a concrete `δ` be frozen.

## 12. Current blockers

R1 remains open until all of the following are documented:

1. one concrete generic escrow transaction environment;
2. its measurable direct failure consequence;
3. its measurable delay consequence;
4. its measurable dispute/recovery consequence;
5. the economically relevant decision threshold;
6. an independently justified numerical `δ`;
7. alpha, power, and sample-size calculation using that frozen `δ`;
8. independent provenance for the consequence evidence.

**Current conclusion:** this protocol advances the research from conceptual `δ` candidates to an auditable economic justification framework. It does not freeze `δ` and does not establish R1 GREEN.

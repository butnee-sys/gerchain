# DEETI R1 — Economic Consequence → Delta Protocol v1

**Status:** PROVISIONAL — NOT FROZEN  
**Stage:** R0 / R1 preparation  
**Branch:** `research/deeti-economic-consequence-v1`

## 1. Purpose

This protocol defines how the practical-effect threshold `δ` for the primary outcome O1 is derived from measurable economic and operational consequences **before confirmatory outcome inspection**.

Primary outcome:

\[
O1 = \frac{N_{completed}}{N_{initiated}}
\]

Practical effect:

\[
\delta = O1_{ET}-O1_{Control}
\]

`δ` is not selected because it produces statistical significance, a convenient sample size, or a desirable result.

## 2. Economic consequence model

For each eligible transaction episode, record consequence components separately:

- `C_direct` — direct monetary cost caused by failure or unsuccessful completion;
- `C_delay` — measurable cost caused by settlement or resolution delay;
- `C_dispute` — measurable cost of dispute handling, recovery, investigation, reversal, or remediation;
- `C_opportunity` — measurable economic opportunity loss attributable to the failed/delayed transaction.

The protocol does **not** assume these components are automatically additive. If components overlap, the overlapping portion must be identified and excluded before aggregation.

A conservative transaction-level consequence is therefore:

\[
C_{failure} = C_{direct}+C_{delay}+C_{dispute}+C_{opportunity}-C_{overlap}
\]

where `C_overlap` is explicitly documented rather than inferred.

## 3. Required measurable quantities

Before δ can be frozen, the selected transaction environment must provide or permit independent measurement of:

1. transaction value;
2. time from initiation to successful settlement;
3. time from initiation to failed/terminated state;
4. direct recovery or remediation cost;
5. dispute-handling cost;
6. externally observable opportunity loss, where applicable;
7. implementation/operation cost attributable to the ET treatment;
8. whether the transaction ultimately satisfies the frozen O1 completion rule.

No quantity may be defined from the observed treatment outcome itself.

## 4. Economic decision rule for δ

Let:

- `C_ET` = incremental cost per transaction of providing the full Escrow Trinity capability;
- `C_failure` = independently measured economic consequence of a non-completed transaction;
- `δ` = absolute improvement in completion probability.

A first-order break-even condition is:

\[
\delta \times C_{failure} \geq C_{ET}
\]

This is a **decision-relevance condition**, not an empirical finding.

It identifies the smallest improvement at which the incremental ET capability can be economically consequential under the selected transaction environment.

If the environment has heterogeneous transaction consequences, the analysis must use the pre-specified expected consequence:

\[
\delta \times E(C_{failure}) \geq E(C_{ET})
\]

with the estimation procedure frozen before confirmatory O1 results are inspected.

## 5. Conservative treatment of uncertainty

If `C_failure` or `C_ET` is uncertain, the protocol must not use the most favorable estimate.

The pre-specified rule should use a conservative bound, such as:

\[
\delta_{economic} = \frac{C_{ET}^{upper}}{C_{failure}^{lower}}
\]

subject to the domain-specific uncertainty model being documented and independently reproducible.

If the denominator is zero, undefined, or not independently measurable, δ cannot be economically justified from this protocol.

## 6. Multiple consequence classes

Where transactions have materially different consequence classes, do not pool them without justification.

Required procedure:

1. define consequence strata before outcome inspection;
2. estimate consequence distributions within each stratum;
3. pre-specify the weighting rule;
4. derive the aggregate expected consequence;
5. perform sensitivity analysis using alternative defensible weighting rules.

## 7. Avoiding double counting

Examples of potential overlap:

- direct financial loss may already include remediation expenditure;
- delay cost may already include lost productive time;
- dispute cost may already include recovery expenditure;
- opportunity loss may incorporate the same delay measured elsewhere.

Therefore every consequence component must have a distinct causal interpretation and measurement source.

## 8. Relation to the falsification test

The protocol creates a falsifiable practical-value condition:

\[
\boxed{\delta_{observed}\times E(C_{failure}) < E(C_{ET})}
\]

would indicate that the observed reliability improvement is insufficient to justify the incremental ET capability under the frozen economic criterion.

This does not falsify every theoretical form of the DEETI hypothesis, but it falsifies the **pre-specified practical-value claim for the selected transaction environment**.

## 9. Prohibited post-outcome adjustments

After confirmatory O1 results are available, the following are prohibited for the primary analysis:

- changing δ because the observed effect is smaller or larger;
- changing consequence weights to improve significance;
- excluding costly failures after seeing treatment results;
- redefining transaction completion;
- changing the economic horizon;
- replacing the selected consequence measure with a more favorable measure.

Such analyses may be exploratory and must be explicitly labelled as such.

## 10. Required freeze record

Before confirmatory outcome collection/inspection, the research record must contain:

- selected transaction domain;
- treatment/control contract;
- O1 coding rule;
- consequence definitions;
- measurement sources and provenance;
- overlap/double-counting rule;
- ET incremental cost definition;
- consequence aggregation rule;
- uncertainty/conservative-bound rule;
- selected δ;
- alpha;
- power target;
- sample-size method;
- missing-data rule;
- analysis version/hash.

## 11. Freeze predicate

Define:

`EconomicMeaning` = every consequence component has a defensible economic interpretation;

`OperationalMeaning` = every component is measurable before outcome inspection;

`NoDoubleCount` = overlap is explicitly handled;

`CostDefined` = incremental ET cost is measurable;

`ConservativeRule` = uncertainty handling is frozen;

`PreOutcomeSpecification` = all choices are recorded before confirmatory outcome inspection.

Then:

\[
\boxed{DeltaEconomicFreeze = EconomicMeaning \land OperationalMeaning \land NoDoubleCount \land CostDefined \land ConservativeRule \land PreOutcomeSpecification}
\]

Only when `DeltaEconomicFreeze = TRUE` may the selected δ be frozen for confirmatory analysis.

## 12. Current status

This protocol freezes the **method for deriving δ**, not the δ value itself.

Current status remains **PROVISIONAL / R0**.

### Next required evidence

Select one concrete generic digital escrow/payment transaction environment and obtain independent pre-outcome evidence sufficient to estimate:

\[
E(C_{failure}),\quad E(C_{ET}),\quad \text{and therefore } \delta_{economic}.
\]

Only after those quantities are justified should the R1 practical-effect and power plan be updated.

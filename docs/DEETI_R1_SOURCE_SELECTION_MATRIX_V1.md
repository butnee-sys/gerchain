# DEETI R1 Data-Source Selection Matrix v1

**Status:** R1 preparation — pre-specified source selection
**Scientific status:** R0
**Date:** 2026-09-17

## 1. Purpose

Select an empirical evidence source without choosing the source because it produces a preferred result.

## 2. Candidate source classes

| Source class | O1 visibility | ETI visibility | Independence risk | Reproducibility | Primary-use status |
|---|---|---|---|---|---|
| Independently auditable transaction/event logs | High | Medium–High | Low–Medium | High | Preferred |
| Independently maintained administrative records | High | Medium | Low–Medium | Medium–High | Preferred |
| Controlled study records | High | High | Medium | High | Preferred when independently audited |
| Independently verifiable research datasets | Variable | Variable | Low | High | Eligible after mapping |
| Human-coded records | Variable | Variable | High | Medium | Secondary unless validated |
| Self-reported survey only | Low for O1 | Medium | High | Medium | Not sufficient alone |
| Marketing/product claims | Low | High apparent / low verifiability | High | Low | Exclude |

## 3. Mandatory eligibility tests

A source is eligible for primary confirmatory use only if:

```text
O1Observable
∧ ETIObservable
∧ TemporalOrderingPossible
∧ ProvenanceTraceable
∧ DefinitionsStable
∧ ComparisonPossible
∧ NegativeOutcomesRetained
∧ CircularityRiskAcceptable
```

## 4. Critical exclusion triggers

Exclude the source from primary confirmatory analysis if any of the following is true and cannot be corrected by an independent validation layer:

1. O1 cannot be reconstructed from transaction lifecycle events;
2. ETI is derived directly from O1;
3. outcome coding changes after outcome inspection;
4. failed/disputed observations are systematically removed;
5. source provenance cannot be established;
6. the comparison group is defined after seeing O1;
7. source definitions change materially without versioned reconciliation.

## 5. Independence test

The source-selection record must identify:

```text
ETI source
O1 source
ETI coding authority
O1 coding authority
independent verification source
```

The strongest primary design is one in which ETI and O1 can be reconstructed independently from the same underlying event history without using the outcome to define the exposure.

## 6. Selection rule

No candidate is selected because its preliminary effect estimate is large, statistically significant, or favorable to H1.

Selection occurs before confirmatory outcome inspection and is based only on:

- eligibility;
- data quality;
- coverage;
- independence;
- reproducibility;
- identification feasibility;
- ethical/legal accessibility.

## 7. Source-selection record

For the selected source, freeze:

```text
source_id
source_owner
coverage_population
coverage_period
ETI_measurement_method
O1_measurement_method
comparison_design
independent_reference
known_limitations
selection_date
selection_version
```

## 8. Gate

```text
CandidateSourcesEnumerated
∧ EligibilityRuleFrozen
∧ ExclusionRuleFrozen
∧ IndependenceAssessed
∧ SelectionMadeBeforeOutcomeInspection
∧ SourceVersionFrozen
```

Passing this gate establishes source-selection readiness only. It does not establish empirical support for H1.

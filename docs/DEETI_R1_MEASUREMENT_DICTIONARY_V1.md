# DEETI R1 Measurement Dictionary v1

**Status:** R1 preparation — operational measurement specification
**Date:** 2026-09-17

## 1. Objective

Turn the registered DEETI hypothesis into observable variables before collecting confirmatory outcome data.

The governing proposition is:

```text
ET = Trust + Transparency + Verified Fulfilment
                 ↓
      DE foundational capability ?
```

## 2. Measurement rule

No variable may be scored after looking at the final outcome in a way that changes its definition.

Every construct requires:

```text
Construct
→ Observable indicator
→ Coding rule
→ Scale
→ Source
→ Missing-data rule
→ Validation test
```

## 3. Trust construct

### T1 — Authority verification

`T1 = verified legitimate authority / required authority`

### T2 — Unauthorized-action resistance

`T2 = 1 - unauthorized material action rate`

### T3 — Counterparty reliability

Pre-specified observed fulfilment/reliability measure, not a post-hoc perception score.

### T4 — Dispute exposure

Inverse-normalized dispute incidence, with direction explicitly documented.

Primary Trust score:

```text
T = mean(T1, T2, T3, T4)
```

Alternative constructions must be retained for sensitivity analysis.

## 4. Transparency construct

### Tr1 — Evidence completeness

`Tr1 = material events with reconstructable evidence / material events`

### Tr2 — Condition visibility

Share of required transaction conditions visible to authorized participants before execution.

### Tr3 — Provenance completeness

Share of material data/value claims with traceable provenance.

### Tr4 — Audit reproducibility

Share of sampled transactions independently reconstructable from retained evidence.

Primary Transparency score:

```text
Tr = mean(Tr1, Tr2, Tr3, Tr4)
```

## 5. Triumph / verified fulfilment construct

Triumph is not measured as subjective “success.” It is operationalized as **verified fulfilment**.

### Tf1 — Condition verification

`Tf1 = eligible conditions independently verified / eligible conditions`

### Tf2 — Correct conditional execution

`Tf2 = correctly executed eligible conditions / verified conditions`

### Tf3 — Settlement completion

`Tf3 = correctly completed settlements / authorized settlements`

### Tf4 — Post-settlement integrity

`Tf4 = 1 - material post-settlement reversal/dispute rate`

Primary verified-fulfilment score:

```text
Tf = mean(Tf1, Tf2, Tf3, Tf4)
```

## 6. Composite ETI

Primary pre-specified index:

```text
ETI = (T + Tr + Tf) / 3
```

Range:

```text
0 ≤ ETI ≤ 1
```

Interpretation:

- `0` = no measured ET capability;
- `1` = maximum measured capability under the operational definitions.

These are measurement endpoints, not qualitative labels of institutions or participants.

## 7. Outcome dictionary

### O1 — Reliability

`O1 = completed governed transactions / initiated governed transactions`

### O2 — Friction

Primary time measure:

`O2a = median transaction completion time`

Secondary friction measures:

- verification time;
- settlement delay;
- direct cost;
- number of required administrative steps.

### O3 — Failure/dispute

`O3 = (failed + materially disputed transactions) / initiated transactions`

### O4 — Evidence integrity

`O4 = independently reconstructable transactions / sampled transactions`

### O5 — Conditional settlement performance

`O5 = correctly authorized settlements after verified conditions / verified eligible conditions`

## 8. Measurement validation before hypothesis testing

R1 requires testing:

1. inter-rater agreement where human coding is used;
2. test-retest stability where repeated scoring is possible;
3. internal consistency where a composite construct is used;
4. convergent validity against relevant observable measures;
5. discriminant validity against unrelated constructs;
6. sensitivity to missing data;
7. sensitivity to alternative reasonable weights.

A high ETI cannot be accepted merely because its components correlate mechanically.

## 9. Data provenance

Each observation must carry:

```text
source_id
source_version
collection_timestamp
transformation_version
measurement_version
observation_id
```

## 10. R1 completion gate

```text
All Constructs Defined
∧ Indicators Observable
∧ Coding Rules Frozen
∧ Primary ETI Formula Frozen
∧ Primary Outcome Frozen
∧ Data Provenance Defined
∧ Missing Data Rule Frozen
∧ Validation Tests Defined
```

Only then may the project claim:

```text
R1 = Operationalized Measurement Model
```

Until that gate is met, research status remains **R0**.

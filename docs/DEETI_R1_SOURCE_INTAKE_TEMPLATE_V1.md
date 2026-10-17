# DEETI R1 Empirical Source Intake Template v1

**Status:** R1 preparation — no source selected
**Scientific status:** R0
**Date:** 2026-09-17

## Purpose

This form is completed for each candidate empirical source before confirmatory outcome inspection. It prevents source selection from being driven by favorable results.

## Candidate identity

```text
source_id:
source_owner:
source_name:
source_version:
access_date:
coverage_period:
coverage_population:
jurisdiction/domain:
```

## Observation structure

```text
observation_unit:
unique_transaction_id_available: yes/no
initiation_event_available: yes/no
completion_event_available: yes/no
condition_events_available: yes/no
settlement_events_available: yes/no
retry_events_available: yes/no
censoring_possible: yes/no
```

## ETI reconstruction

For each component specify the exact source field/event and transformation:

```text
Trust:
  source field/event:
  transformation:

Transparency:
  source field/event:
  transformation:

Verified fulfilment:
  source field/event:
  transformation:
```

## O1 reconstruction

```text
Initiated definition:
Completed definition:
Failure definition:
Dispute definition:
Censoring rule:
Duplicate/retry rule:
```

## Independence / circularity

```text
ETI uses final O1 state: yes/no
O1 uses final ETI state: yes/no
Same authority defines ETI and O1: yes/no
Independent verification available: yes/no
Temporal ordering satisfied: yes/no
```

If any answer creates material circularity, the source cannot enter the primary confirmatory dataset until the problem is resolved.

## Comparison feasibility

```text
ET exposure variation:
comparison group:
assignment mechanism:
confounding risks:
matching/stratification possible:
quasi-experiment possible:
intervention possible:
```

## Quality

```text
completeness:
accuracy:
timeliness:
provenance:
consistency:
independence:
reproducibility:
known limitations:
```

## Decision

One of:

```text
PRIMARY_ELIGIBLE
SECONDARY_ONLY
EXPLORATORY_ONLY
REJECTED
```

The decision must be made before inspecting the primary O1 result.

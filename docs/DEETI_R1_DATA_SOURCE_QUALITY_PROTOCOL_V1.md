# DEETI R1 Data Source Quality Protocol v1

**Status:** R1 preparation
**Scientific status:** R0
**Date:** 2026-09-17

## 1. Purpose

The DEETI claim cannot be tested credibly unless the evidence source itself is independently characterized. This protocol separates source quality from the ETI score.

## 2. Source-quality dimensions

Each candidate source is assessed on:

- **Completeness:** proportion of required transaction lifecycle events available.
- **Accuracy:** agreement with an independently verifiable reference where available.
- **Timeliness:** delay between event occurrence and recorded observation.
- **Provenance:** ability to trace each observation to its originating record.
- **Consistency:** stability of definitions and coding across the study period.
- **Independence:** degree to which the source is independent of the ETI measurement process.
- **Reproducibility:** ability for an independent analyst to reconstruct the dataset.

## 3. Source acceptance rule

A source may enter the primary dataset only when its limitations are documented and none of its known limitations directly invalidate O1 measurement.

A source that measures ETI and O1 through the same unverified process creates circularity risk and should not be used as the sole primary evidence source.

## 4. Source hierarchy

Preferred order:

1. independently auditable machine event records;
2. independently maintained administrative records;
3. independently verified research datasets;
4. controlled study records;
5. human-coded records with inter-rater validation.

A lower-ranked source is not automatically rejected; it requires stronger validation and explicit limitation reporting.

## 5. Source-quality record

Each source must have:

```text
source_id
source_owner
source_version
coverage_period
coverage_population
known_exclusions
definition_version
extraction_method
quality_assessment_date
quality_limitations
independent_reference_available
```

## 6. Independence rule

At least one component of the primary evidence chain should be independently verifiable. If the same mechanism defines ETI, determines O1, and verifies the outcome, the study must explicitly model this dependence or the claim is considered vulnerable to measurement circularity.

## 7. Gate

```text
SourceDefined
∧ CoverageKnown
∧ ProvenanceTraceable
∧ DefinitionsStable
∧ O1Measurable
∧ CircularityRiskAssessed
∧ LimitationsRecorded
```

Passing this gate means the source is eligible for consideration. It does not establish that the source is unbiased or that H1 is true.

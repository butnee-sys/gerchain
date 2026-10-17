# DEETI R1 Empirical Source Shortlist v1

**Status:** Candidate-source shortlist — no source selected yet
**Scientific status:** R0
**Date:** 2026-09-17

## 1. Candidate A — Controlled escrow transaction records

**Target:** A real escrow/conditional-settlement environment where transaction lifecycle events are independently logged.

**Required evidence:** initiation, ETI-relevant conditions, execution, settlement/closure, failures, disputes, timestamps, transaction value/complexity.

**Strength:** Directly matches the proposed DEETI mechanism.

**Main risk:** The same platform may define ETI and O1, creating circularity.

**Primary eligibility:** Yes, only if an independent audit/reference layer exists.

## 2. Candidate B — Payment/settlement administrative records

**Target:** Independently maintained payment or settlement records with transaction-level completion/failure outcomes.

**Strength:** Strong O1 observability and potentially large sample size.

**Main limitation:** ETI components may not be directly observable and may require validated reconstruction.

**Primary eligibility:** Potentially; ETI measurement must be independently operationalized.

## 3. Candidate C — Insurance claim / conditional settlement records

**Target:** Claims or conditional payment episodes with verification, authorization, settlement, dispute, and closure events.

**Strength:** Naturally contains conditions, verification, evidence, and conditional fulfilment.

**Main limitation:** Domain-specific; generalization to Digital Economy requires explicit boundary conditions.

**Primary eligibility:** Potentially strong for a domain test, not by itself evidence of universal foundational status.

## 4. Candidate D — Controlled digital service intervention

**Target:** A prospective implementation in which ET capability is introduced while a comparable control process remains observable.

**Strength:** Stronger causal identification than passive observational data.

**Main limitation:** Requires real operational access and pre-intervention baseline.

**Primary eligibility:** Preferred if feasible and ethically/legally approved.

## 5. Candidate E — Public research/administrative dataset

**Target:** An independently accessible dataset containing transaction reliability and sufficient variables to reconstruct ETI or validated proxies.

**Strength:** Independent reproducibility.

**Main limitation:** ETI may be incompletely observable.

**Primary eligibility:** Eligible only after construct-mapping validation.

## 6. Candidate F — Survey-only evidence

**Target:** Perceived trust/transparency/satisfaction surveys.

**Strength:** Potentially easy to collect.

**Main limitation:** Does not directly observe O1 and is vulnerable to common-method bias.

**Primary eligibility:** Secondary/exploratory only; not sufficient for the primary foundational test.

## 7. Selection rule

No candidate is selected yet.

The final source must satisfy the frozen source-selection matrix and provide a defensible separation between:

```text
ETI measurement
      ≠
O1 outcome measurement
```

A source may be selected only before confirmatory outcome inspection.

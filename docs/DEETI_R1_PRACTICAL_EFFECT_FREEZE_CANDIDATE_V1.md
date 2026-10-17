# DEETI R1 Practical Effect Freeze Candidate v1

**Status:** CANDIDATE — NOT FROZEN
**Scientific stage:** R0 / R1 preparation

## Purpose

Define the decision rule for selecting the minimum practically meaningful improvement in primary outcome O1 before confirmatory outcome inspection.

## Primary outcome

`O1 = completed governed transactions / initiated governed transactions`

## Candidate practical-effect rule

For a binary completion outcome, define:

`delta = minimum absolute increase in completion probability that changes an economic or operational decision.`

The selected delta must not be justified by statistical convenience alone.

## Evidence required to freeze delta

At least one pre-outcome source is required for each claimed consequence:

1. **Direct operational consequence** — measurable reduction in failed, delayed, or unresolved transactions.
2. **Economic consequence** — measurable reduction in transaction cost, delay cost, dispute cost, or other declared economic loss.
3. **Decision threshold** — an independent reason why an improvement below delta would not justify adoption of the ET capability.
4. **Uncertainty boundary** — plausible range and assumptions must be recorded.

## Candidate values for planning only

The following are scenario values, not the selected delta:

- delta = 0.02
- delta = 0.03
- delta = 0.05

They must not be treated as empirical findings.

## Freeze prohibition

After confirmatory outcomes are inspected, delta MUST NOT be revised to obtain a preferred conclusion.

## Required freeze record

Before confirmatory testing, record:

- baseline O1 source;
- operational consequence supporting delta;
- economic consequence supporting delta;
- decision-maker or adoption threshold;
- source citations/provenance;
- uncertainty assumptions;
- selected delta;
- date and commit hash;
- confirmation that confirmatory outcomes were not inspected when delta was selected.

## Current decision

No delta is frozen yet.

Reason: the primary empirical environment and real-stake consequence have not yet been fixed sufficiently to justify a decision-relevant threshold.

## Next step

Specify one concrete generic escrow transaction protocol with a real or consequential stake, then derive the practical-effect threshold from the pre-treatment economic consequence of transaction failure or non-completion.

# DEETI R1 Primary Outcome Selection v1

**Status:** Decision pending — do not select after inspecting empirical results

The foundational capability hypothesis concerns whether ET improves the reliability and verifiability of digital economic activity while reducing friction. A single primary outcome must nevertheless be selected before confirmatory testing.

## Candidate primary outcomes

### Option A — Transaction reliability

```text
O1 = completed governed transactions / initiated governed transactions
```

Strength: directly reflects successful completion.

Limitation: may show ceiling effects in mature systems.

### Option B — Transaction completion time

```text
O2a = median transaction completion time
```

Strength: directly captures friction.

Limitation: strongly affected by transaction complexity and external conditions.

### Option C — Failure/dispute rate

```text
O3 = (failed + materially disputed transactions) / initiated transactions
```

Strength: directly captures breakdown of transaction execution.

Limitation: dispute classification may vary by domain.

### Option D — Evidence integrity

```text
O4 = independently reconstructable transactions / sampled transactions
```

Strength: closely matches the transparency component.

Limitation: risks circularity if transparency is defined using the same evidence.

### Option E — Conditional settlement performance

```text
O5 = correctly authorized settlements after verified conditions / verified eligible conditions
```

Strength: directly tests conditional execution.

Limitation: domain applicability may be narrower.

## Selection rule

The primary outcome must be selected using **theoretical relevance, measurement validity, observability, variation, independence from ETI construction, and practical significance** — not by choosing whichever outcome produces the largest effect.

Once selected, the primary outcome must be frozen before confirmatory outcome analysis.

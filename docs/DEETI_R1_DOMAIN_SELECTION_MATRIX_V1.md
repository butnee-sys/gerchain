# DEETI R1 Domain Selection Matrix v1

**Status:** Provisional
**Scientific status:** R0

## Candidate domains

| Candidate | ETI manipulation | O1 measurement | Temporal ordering | Real consequence | Independent verification | Main limitation |
|---|---|---|---|---|---|---|
| Escrow/payment transaction | High | High | High | High | High | Access, legal/ethical controls |
| Digital service/data transaction | High | High | High | Medium–High | High | Outcome definition may be domain-specific |
| SHUUD/SHIID-like application | High | High | High | High | Potentially high | Product-specific confounding |

## Selection rule

Primary domain must maximize experimental identification while minimizing construct contamination.

Required properties:

`ETI manipulable ∧ O1 independently measurable ∧ temporal precedence ∧ real consequence ∧ auditable provenance`

## Current decision

The preferred primary domain class is a **generic escrow/payment transaction**, because it permits the cleanest separation between:

`Escrow Trinity capability → transaction lifecycle → settlement reliability`

SHUUD/SHIID should remain a possible later application-domain replication, not the first foundational test.

## Why not SHUUD first?

SHUUD contains application-specific effects: road context, insurance, AI confirmation, operator behavior, traffic conditions, and user behavior. These can obscure whether an observed effect is attributable to the Escrow Trinity capability itself.

## Scientific interpretation

This matrix is a design selection, not evidence that ETI improves O1. No foundational capability claim is validated by this document.

## Next freeze requirements

1. Concrete transaction protocol.
2. Treatment/control specification.
3. Participant and transaction population.
4. Real-stake or consequential settlement mechanism.
5. Independent O1 coding.
6. Pre-treatment δ.
7. Alpha, power, sample size.
8. Data provenance and audit procedure.

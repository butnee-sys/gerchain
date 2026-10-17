# CORE W2 — Independent Oracle Contract

## Purpose

The oracle is outside the GerChain execution path. It determines the expected economic result independently of PostgreSQL persistence, idempotency, witness, escrow, and release implementation.

## C2 oracle

Input:

`capacity, ordered distinct requests`

For each request, commit the request iff it is no greater than the remaining capacity; otherwise commit zero.

Invariant:

`sum(committed) <= capacity`

For `(capacity=2_000_000, requests=(1_500_000, 1_500_000))`, the expected committed vector is `(1_500_000, 0)`.

The production implementation may serialize the winner differently, but its economic committed total must agree with the oracle and must never exceed capacity.

## C6 oracle

A decision is executable only if the canonical relevant state at execution is semantically identical to the state used to produce the decision.

`decision_state != current_state -> HOLD/REJECT_STALE`

The oracle intentionally uses direct semantic equality rather than GerChain fingerprinting, PostgreSQL locking, or operation idempotency.

## Independence rule

`Oracle != CORE`

The oracle must not import persistence implementation, call production release services, reuse production fingerprints, or inspect production operation outcomes to decide the expected result.

Agreement with the oracle is necessary but not sufficient for W2 GREEN; adversarial PostgreSQL execution and independent reproduction remain required.

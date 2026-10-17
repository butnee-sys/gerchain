# CORE W3 — Schema Concurrency Contract

## Scope

CORE only. SHUUD is out of scope.

W3 validates that concurrent schema/version state transitions cannot produce incompatible authoritative schema state, lost updates, split-brain version authority, or unsafe execution during an upgrade boundary.

## Claim

For a canonical schema/version authority, concurrent readers and writers must observe a valid version transition, and at most one authoritative upgrade may commit for a given predecessor state.

## Canonical state

`SchemaState = (SchemaID, CurrentVersion, StateHash, Status, UpdatedAt)`

`Upgrade = (UpgradeID, FromVersion, ToVersion, Preconditions, MigrationHash, Authority, Status)`

## Invariants

- **I-W3.1 — Single authority:** one canonical current schema version exists for a schema identity.
- **I-W3.2 — No lost upgrade:** an accepted upgrade cannot be silently overwritten by a concurrent upgrade.
- **I-W3.3 — No split-brain:** committed readers do not observe two authoritative current versions for the same schema identity.
- **I-W3.4 — Valid predecessor:** an upgrade from version V is accepted only against the expected canonical predecessor V.
- **I-W3.5 — Atomic transition:** schema version and associated migration state commit atomically.
- **I-W3.6 — Idempotent retry:** retrying the same upgrade identity does not create a second authoritative transition.
- **I-W3.7 — Conflict isolation:** distinct incompatible upgrades cannot both commit from the same predecessor.
- **I-W3.8 — Reader safety:** a committed execution never relies on a partially committed schema transition.

## Falsification

W3 is RED if any of the following occurs:

- two incompatible upgrades both become authoritative;
- a committed schema version regresses unexpectedly;
- a valid upgrade is lost without explicit rejection;
- reader observes an impossible intermediate schema authority;
- migration state and schema version commit inconsistently;
- duplicate upgrade creates multiple authoritative transitions;
- concurrent upgrade bypasses predecessor/version precondition.

## Required adversarial vectors

1. Two concurrent distinct upgrades from the same predecessor.
2. Same upgrade identity retried concurrently.
3. Reader concurrent with upgrade.
4. Upgrade followed by retry after commit ambiguity.
5. Failed migration with rollback.
6. Version conflict / stale predecessor.
7. Concurrent schema metadata update and authoritative state read.

## Oracle

The W3 oracle must be outside production schema/version mutation code. It evaluates the allowed state-transition relation independently:

`Valid(V -> V') iff predecessor(V) ∧ authorized(V') ∧ atomic(V,V')`

Agreement must be evaluated on invariants and final authoritative state, not implementation internals.

## Evidence chain

`Contract -> Production implementation -> PostgreSQL adversarial test -> Independent oracle -> Deterministic reproduction -> Independent re-performance -> Evidence reconciliation -> GREEN`

## Exit criteria

All W3 invariants pass under the declared test domain; independent oracle agrees; independent re-performance reproduces the state-transition invariants; evidence is tied to the exact execution commit; no unresolved critical contradiction remains.

W3 GREEN does not imply final CORE GREEN or CORE LOCK.

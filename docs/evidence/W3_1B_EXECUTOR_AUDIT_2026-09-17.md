# CORE W3.1-B Executor Audit — 2026-09-17

## Audit finding

The first W3.1-B executor implementation contained an unsafe recovery shortcut: if the target physical schema already existed without a committed W3 authority record, the executor could reconcile that target and publish the authority record without provenance that the DDL had been executed by the authoritative executor.

This is incompatible with the frozen recovery boundary. Recovery must first establish that the recorded predecessor physical state is intact. A target schema existing without an authority record is an ambiguous external state and must not be silently adopted.

## Correct invariant

For a new migration:

`RecordedPredecessorFingerprint == ActualFingerprint BEFORE DDL`

must hold before any migration DDL is executed.

After DDL:

`ActualFingerprint == ExpectedSuccessorFingerprint`

must hold before W3 authority advancement.

If the predecessor does not match, execution stops before DDL. If an external target schema is already present, it is therefore rejected rather than adopted.

## Required falsification cases

- F7: failed migration rolls back; retry from intact predecessor can succeed.
- F11: committed authority without physical schema is rejected.
- F12: physical DDL without committed authority is detected/rejected; no implicit authority adoption.

## Status

This audit finding blocks W3.1-B scientific closure until the executor and tests are repaired and independently re-performed.

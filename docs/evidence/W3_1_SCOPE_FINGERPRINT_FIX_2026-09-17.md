# W3.1 Scope-Fingerprint State Tracking Fix

Date: 2026-09-17

## Defect

The independent PostgreSQL re-performance captured the D-type-mutation fingerprint, then continued through E1-E5 semantic mutations, and later incorrectly compared the current schema fingerprint to the historical D fingerprint. This made the G scope-isolation assertion compare different schema states.

## Repair

The test now captures `before_scope_fingerprint` after all E1-E5 mutations and immediately before the out-of-scope schema mutation. Scope isolation is asserted against that same current in-scope schema state before and after the outside-schema mutation.

## Expected invariant

`Fingerprint(S) = Fingerprint(S ∪ O)` for `O ∉ Scope`, with both observations referring to the same in-scope semantic state.

The repair is test-state tracking only. It does not constitute W3.1-A GREEN. Full CI, cross-agreement, fresh-process determinism, independent reproduction, and evidence reconciliation remain required.

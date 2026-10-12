# Three-Selector and Checksum Reconciliation Register

**Status:** EVIDENCE-BASED SNAPSHOT — NOT A PRODUCTION LOCK  
**Repository:** `butnee-sys/gerchain`  
**Comparison timestamp:** 2026-10-12  
**Reference A (main):** `621e7e2acefe243d4c72e783970e1eb833c60b96`  
**Reference B (feature branch):** `0dd86d480cb5833c6ac6b352f992a10b867dd0f4` (`feat/ea21-transaction-aware-ledger`)

## 1. Unified selector/checksum table

The identifiers below are GitHub content blob IDs (Git SHA-1), **not SHA-256 file digests**. They provide exact content identity for the selected files. A future SHA-256 column must be populated from the raw file bytes by a reproducible hashing step; it must not be inferred from a Git blob ID.

| Selector | Authoritative source file | Reference A blob ID | Reference B blob ID | Exact content comparison | Verified difference |
|---|---|---|---|---|---|
| NEF — asset truth adapter | `nef_gerchain_port/nef_adapter.py` | `432eae1f843c3648f676e5db9664f0eba71cc8fe` | `432eae1f843c3648f676e5db9664f0eba71cc8fe` | IDENTICAL | 0 content difference in this file |
| G-3 Escrow — condition/policy foundation | `architecture/g3_core.py` | `2ca081a440ff56e461c67e7bf4ecc2a9c55c95be` | `2ca081a440ff56e461c67e7bf4ecc2a9c55c95be` | IDENTICAL | 0 content difference in this file |
| GerChain CORE — runtime/value-flow boundary | `services/gerchain_runtime.py` | `e6d57e235dd4cc7ab273fb5c65a59c8d9de62d57` | `655670944a78db7af4bc60d8c2a758d7ad507a53` | DIFFERENT | Reference A: 193 lines; Reference B: 563 lines; net +370 lines in the selected file |

## 2. Interpretation of the exact result

1. **NEF selector:** selected adapter file is byte-for-byte identical between the two refs.
2. **G-3 selector:** selected policy/core file is byte-for-byte identical between the two refs.
3. **GerChain CORE selector:** runtime file differs; its implementation grew from 193 to 563 lines. This establishes a content difference, but not by itself that every added line is correct or production-verified.
4. This is a **three-file selector comparison**, not a claim that every file in each subsystem is identical or different.
5. The GitHub compare endpoint reports Reference B as 3,499 commits ahead of Reference A. That branch-level count must not be treated as a count of changes in these three selectors. The table reports only the directly fetched file content IDs and line counts.
6. The frozen architecture document remains the architectural authority. These selectors do not replace the frozen layer boundaries or authorize an architecture change.

## 3. Checksum contract and next verification gate

To make the register cryptographically reproducible, the next pass must record, for each exact ref and each selected file:

- repository + branch/commit SHA;
- path;
- Git blob ID (SHA-1, as above);
- SHA-256 of the raw file bytes;
- byte length and line count;
- comparison result and, for changed files, a complete unified diff;
- execution/test evidence pinned to the exact commit.

**Do not compare SHA-256 values against Git blob IDs.** Git blob IDs hash Git's blob representation; they are a different checksum contract from a raw-file SHA-256.

## 4. Release status

**Selector reconciliation: PARTIALLY VERIFIED.** Exact identity is established for all three selected files; the CORE runtime file is different.  
**SHA-256 registry: OPEN.** No raw-file SHA-256 has been asserted in this document.  
**Full subsystem reconciliation: OPEN.** The selected file comparison is not a complete recursive source inventory.  
**Production lock: NOT AUTHORIZED by this evidence alone.**

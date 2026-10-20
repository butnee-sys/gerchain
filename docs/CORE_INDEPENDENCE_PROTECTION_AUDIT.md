# Step 3 — CORE Independence & Protection Audit

**Status:** IN PROGRESS / NOT LOCKED  
**Scope:** Fundamental infrastructure only. Product/application layers are excluded.  
**Canonical architecture:** `docs/DEE_ARCHITECTURE_FREEZE.md`  
**Production authority freeze:** `docs/EA34_LEGACY_VALUE_AUTHORITY_FREEZE.md`

## 1. Protection invariant

> NO DOWNSTREAM ACTOR MAY ALTER THE AUTHORITATIVE TRUTH, AUTHORITY, POLICY, OR CORE EXECUTION STATE OF PDEIZ DIRECTLY.

PDEIZ is a protective-zone concept over NEF + G3 + GerChain, not a new canonical architecture layer. Requests for service may cross a controlled interface; requests to mutate protected truth, authority, policy, or core mechanisms must be denied.

## 2. Evidence reviewed

- `architecture/contracts.py`: typed `BoundaryRequest` / `BoundaryResponse`; the contract itself does not authorize operations.
- `architecture/g3_core.py`: validates required asset, condition-policy and escrow mappings, then forwards to an injected Core handler; it does not create a second operational engine.
- `architecture/nef_gerchain.py`: validates NEF asset references and rejects non-VALID asset status.
- `services/g3_dee_authorized_handler.py`: requires APPROVE, a `SignedRelease`, a manifest and successful DEE authorization before forwarding.
- `services/g3_core_handler.py`: requires G3 Trinity PASS, APPROVE, AUTHORIZED, DEE authorization context and release evidence before calling the existing runtime.
- `docs/EA34_LEGACY_VALUE_AUTHORITY_FREEZE.md`: names Canonical Ledger as the only production value authority and freezes legacy stores as non-authoritative.
- `docs/DEE_ARCHITECTURE_FREEZE.md`: freezes the layer sequence and explicit adapter boundaries.

## 3. Findings

### P3-01 — Core engine duplication boundary

**Assessment: PASS at the inspected adapter/handler boundary.** G3/Core adapters inject the existing Core handler/runtime rather than implementing another Ledger or Escrow engine.

### P3-02 — Asset-truth boundary

**Assessment: PASS at the inspected NEF adapter.** An asset must carry identity, valuation, verification, version and a VALID status before forwarding.

### P3-03 — Release authorization gate

**Assessment: PASS at the inspected release handler path.** Release requires DEE authorization context, APPROVE, AUTHORIZED and all three G3 Trinity conditions.

### P3-04 — Generic adapter is not itself a protection policy

**Assessment: OPEN.** `GovernedBoundaryAdapter.handle()` validates request/response types and forwards the request. It does not classify downstream requests as service requests versus protected-state mutation requests. Protection therefore depends on the specific downstream handler and its policy gates; the generic adapter alone is not proof of PDEIZ protection.

### P3-05 — End-to-end protection tests

**Assessment: OPEN.** The inspected sources establish component-level gates, but no exact-SHA test evidence was retrieved in this audit proving the full negative matrix below.

## 4. Required falsification matrix

| Test | Required result |
|---|---|
| Downstream asks for a permitted service through the published boundary | Allow only after validation and authorization |
| Downstream attempts direct Ledger/balance mutation outside Canonical Ledger | Deny / fail closed |
| Downstream attempts direct Escrow state mutation outside the canonical aggregate | Deny / fail closed |
| Downstream attempts to replace NEF asset truth or downgrade its verification | Deny |
| Downstream attempts to alter G3 policy or grant itself authority | Deny |
| Missing/invalid DEE authorization, manifest, decision or Trinity condition | Deny / fail closed |
| Alternate/in-memory runtime is selected as production value authority | Boot or operation fails closed |
| Recovery process attempts to create alternate authoritative truth | Deny; remain HOLD until canonical verification passes |
| A rejected layer returns a denial | No downstream call occurs |
| A boundary response has the wrong type | Reject; do not continue flow |

## 5. Lock criteria

Step 3 cannot be locked until:
1. Each negative case above has an executable test.
2. Tests run against the exact branch-tip SHA and results are retrieved.
3. No new authoritative Ledger, Escrow, Witness or policy owner is introduced.
4. Production runtime refuses legacy/in-memory authority.
5. Any unresolved recovery verification remains HOLD.
6. Evidence is recorded with exact commit SHA, test command, and CI run URL.

## 6. Current conclusion

Component-level separation and several fail-closed release/asset gates are present. However, the generic boundary adapter is only a typed forwarding boundary, and the full PDEIZ protection matrix has not been proven by retrieved exact-SHA test evidence.

**Step 3: IN PROGRESS / NOT LOCKED.**  
**Overall fundamental architecture + EAI: NOT LOCKED.**

Next action: implement and run the protection falsification tests without introducing a new canonical architecture layer or duplicating any authoritative engine.

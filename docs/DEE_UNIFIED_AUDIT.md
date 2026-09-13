# DEE Unified Audit

## Principle

DEE must provide one tamper-evident audit chain across governance, authorization, connector entry, execution, and recovery. Audit is a trace of authority and execution; it is not an independent authority.

## Minimum audit context

Each record carries:

- sequence and timestamp
- event and decision
- change/request identity
- Owner identity
- stage
- connector identity when applicable
- operation
- Trinity proof
- previous record hash
- current record hash

For protected execution stages, proof context is first-class audit data rather than text embedded in an operation field:

- `SETTLEMENT` requires `witness_state_root` and `settlement_hash`
- `RECOVERY` requires `witness_state_root`, `settlement_hash`, and `recovery_decision_hash`
- `RELEASE` requires all three plus `execution_chain_hash`

The canonical protected execution linkage is:

`Witness State Root → Settlement Hash → Recovery Decision Hash → Execution Chain Hash → Audit Record Hash`

## Chain rule

`GENESIS → Root of Trust → Governance → Authorization → Protection → Execution → Audit / Recovery`

Each record commits to the previous record hash. Tampering with a record or its governance context invalidates the chain.

## Security rule

Audit records do not contain raw connector credentials or private keys. Audit failure must never be used to manufacture authorization. A missing or invalid audit record is evidence of a security failure, not permission to continue.

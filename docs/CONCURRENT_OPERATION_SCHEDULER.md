# Concurrent operation scheduler

`core.concurrent_operations.execute_concurrently` runs independent callables with bounded parallelism.

## Contract

- Operations with disjoint `resource_keys` may execute concurrently.
- Operations sharing a resource key execute serially in submission order.
- Results are returned in input order, regardless of completion order.
- Exceptions become explicit `FAILED` results; other operations continue.
- There are no implicit retries, and operation IDs must be unique.
- Callers must declare every shared mutable resource accurately.

Example:

```python
from core.concurrent_operations import OperationSpec, execute_concurrently

results = execute_concurrently(
    [
        OperationSpec("refresh-A", frozenset({"account:A"}), refresh_a),
        OperationSpec("refresh-B", frozenset({"account:B"}), refresh_b),
    ],
    max_workers=4,
)
```

## Financial correctness boundary

This scheduler is **not** a transaction coordinator. Do not split a single value-moving operation into separate scheduled callables. Ledger movement, escrow transition, witness evidence, idempotency, and outbox insertion that represent one operation must remain in the same database transaction through `AtomicValueTransaction`. Concurrent operations that touch the same escrow or account must use the same resource key (for example, `escrow:E-123` or `account:A-123`) if this scheduler is used around them. Database locks, constraints, idempotency, and transaction boundaries remain the final correctness controls; in-process resource keys do not coordinate across multiple application processes.

## Verification

Tests cover concurrent execution of disjoint resources, serialization for shared resources, stable result ordering, failure reporting, duplicate IDs, invalid worker counts, and an empty batch. A passing local test run or CI run must be recorded separately; creating these files is not test evidence.
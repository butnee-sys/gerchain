"""Bounded concurrency for independent operations with resource-level serialization.

This module schedules work; it is not a transaction coordinator and must not be
used to split one value-moving operation across independent workers. Coupled
Ledger/Escrow/Witness/Outbox changes must remain inside AtomicValueTransaction.
"""
from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from typing import Callable, Generic, Iterable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class OperationSpec(Generic[T]):
    """One callable and the resources it may mutate.

    Operations sharing any resource key are serialized in submission order.
    Operations with disjoint keys may run concurrently.
    """

    operation_id: str
    resource_keys: frozenset[str]
    execute: Callable[[], T]


@dataclass(frozen=True)
class OperationResult(Generic[T]):
    operation_id: str
    status: str
    value: T | None = None
    error: str | None = None


def execute_concurrently(
    operations: Iterable[OperationSpec],
    *,
    max_workers: int = 4,
) -> list[OperationResult]:
    """Execute independent operations concurrently with bounded workers.

    Results preserve input order. A failed operation is captured as FAILED and
    does not discard other results. There are no implicit retries. Callers must
    supply accurate resource keys; shared keys are a serialization contract.
    """
    if isinstance(max_workers, bool) or not isinstance(max_workers, int) or max_workers < 1:
        raise ValueError("max_workers must be a positive integer")

    pending = list(operations)
    ids = [item.operation_id for item in pending]
    if any(not isinstance(item.operation_id, str) or not item.operation_id.strip() for item in pending):
        raise ValueError("operation_id must be a non-empty string")
    if len(set(ids)) != len(ids):
        raise ValueError("operation_id values must be unique")
    for item in pending:
        if not callable(item.execute):
            raise ValueError(f"operation {item.operation_id!r} has no callable execute")
        if any(not isinstance(key, str) or not key.strip() for key in item.resource_keys):
            raise ValueError(f"operation {item.operation_id!r} has an invalid resource key")

    if not pending:
        return []

    result_by_id: dict[str, OperationResult] = {}
    active: dict[Future, OperationSpec] = {}
    active_resources: set[str] = set()
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="gerchain-op") as pool:
        while pending or active:
            # Scan only in submission order. A conflicting later operation
            # cannot overtake an earlier pending operation on the same resource.
            scan_index = 0
            blocked_resources: set[str] = set()
            while scan_index < len(pending) and len(active) < max_workers:
                spec = pending[scan_index]
                if (
                    spec.resource_keys.isdisjoint(active_resources)
                    and spec.resource_keys.isdisjoint(blocked_resources)
                ):
                    future = pool.submit(spec.execute)
                    active[future] = spec
                    active_resources.update(spec.resource_keys)
                    pending.pop(scan_index)
                    continue
                # A later operation must not overtake an earlier pending
                # operation that shares any resource, even if the earlier one
                # is temporarily blocked by a different active resource.
                blocked_resources.update(spec.resource_keys)
                scan_index += 1
            # pending is mutated as tasks are submitted, so the first remaining
            # item is always the earliest not-yet-submitted operation.
            if not active:
                # No active work means a pending item should always be runnable;
                # guard against scheduler regressions instead of hanging.
                raise RuntimeError("concurrency scheduler stalled with pending operations")
            completed, _ = wait(active, return_when=FIRST_COMPLETED)
            for future in completed:
                spec = active.pop(future)
                active_resources.difference_update(spec.resource_keys)
                try:
                    result_by_id[spec.operation_id] = OperationResult(
                        operation_id=spec.operation_id,
                        status="SUCCEEDED",
                        value=future.result(),
                    )
                except Exception as exc:  # operation failures are returned, not hidden
                    result_by_id[spec.operation_id] = OperationResult(
                        operation_id=spec.operation_id,
                        status="FAILED",
                        error=f"{type(exc).__name__}: {exc}",
                    )

    # Submission order is retained independently of scheduler completion order.
    return [result_by_id[operation_id] for operation_id in ids]

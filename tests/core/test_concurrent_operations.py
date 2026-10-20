from threading import Barrier, Event

import pytest

from core.concurrent_operations import OperationSpec, execute_concurrently


def test_disjoint_resources_run_concurrently_and_results_keep_input_order():
    barrier = Barrier(2)

    def work(value):
        barrier.wait(timeout=2)
        return value

    results = execute_concurrently(
        [
            OperationSpec("first", frozenset({"account:A"}), lambda: work("A")),
            OperationSpec("second", frozenset({"account:B"}), lambda: work("B")),
        ],
        max_workers=2,
    )
    assert [(r.operation_id, r.status, r.value) for r in results] == [
        ("first", "SUCCEEDED", "A"),
        ("second", "SUCCEEDED", "B"),
    ]


def test_shared_resource_is_serialized_in_submission_order():
    first_done = Event()

    def first():
        first_done.set()
        return "first"

    def second():
        assert first_done.is_set()
        return "second"

    results = execute_concurrently(
        [
            OperationSpec("first", frozenset({"escrow:E1"}), first),
            OperationSpec("second", frozenset({"escrow:E1", "ledger:A"}), second),
        ],
        max_workers=2,
    )
    assert [r.value for r in results] == ["first", "second"]


def test_failure_is_reported_without_losing_other_results():
    def fail():
        raise RuntimeError("expected failure")

    results = execute_concurrently(
        [
            OperationSpec("bad", frozenset({"A"}), fail),
            OperationSpec("good", frozenset({"B"}), lambda: 7),
        ],
        max_workers=2,
    )
    assert results[0].status == "FAILED"
    assert results[0].error == "RuntimeError: expected failure"
    assert results[1].status == "SUCCEEDED"
    assert results[1].value == 7


def test_duplicate_operation_ids_are_rejected_before_execution():
    with pytest.raises(ValueError, match="must be unique"):
        execute_concurrently(
            [
                OperationSpec("same", frozenset(), lambda: 1),
                OperationSpec("same", frozenset(), lambda: 2),
            ]
        )


def test_invalid_worker_count_is_rejected():
    with pytest.raises(ValueError, match="positive integer"):
        execute_concurrently([], max_workers=0)


def test_empty_batch_returns_empty_results():
    assert execute_concurrently([]) == []

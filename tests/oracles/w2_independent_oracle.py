from dataclasses import dataclass


@dataclass(frozen=True)
class LiquidityOracleResult:
    committed: tuple[int, ...]
    capacity: int

    @property
    def over_allocated(self) -> bool:
        return sum(self.committed) > self.capacity

    @property
    def conservation_holds(self) -> bool:
        return sum(self.committed) <= self.capacity


def solve_distinct_consumers(*, capacity: int, requests: tuple[int, ...]) -> LiquidityOracleResult:
    """Independent sequential economic oracle; no GerChain persistence imports."""
    remaining = capacity
    committed: list[int] = []
    for request in requests:
        if request <= remaining:
            committed.append(request)
            remaining -= request
        else:
            committed.append(0)
    return LiquidityOracleResult(tuple(committed), capacity)


def stale_decision_is_safe(*, decision_state: dict, current_state: dict) -> bool:
    """Independent semantic oracle: changed relevant state invalidates execution."""
    return decision_state == current_state

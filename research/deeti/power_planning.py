"""DEETI R1 planning calculation for a simple two-group binary endpoint.

Illustrative planning tool only. Values are not empirical evidence.
"""

from __future__ import annotations

from math import sqrt
from statistics import NormalDist


def required_n_per_group(p0: float, delta: float, alpha: float = 0.05, power: float = 0.80) -> int:
    if not (0 < p0 < 1):
        raise ValueError("p0 must be between 0 and 1")
    p1 = p0 + delta
    if not (0 < p1 < 1):
        raise ValueError("p0 + delta must be between 0 and 1")
    if not (0 < alpha < 1 and 0 < power < 1):
        raise ValueError("alpha and power must be between 0 and 1")
    z_alpha = NormalDist().inv_cdf(1 - alpha / 2)
    z_power = NormalDist().inv_cdf(power)
    p_bar = (p0 + p1) / 2
    numerator = (
        z_alpha * sqrt(2 * p_bar * (1 - p_bar))
        + z_power * sqrt(p0 * (1 - p0) + p1 * (1 - p1))
    ) ** 2
    return int(numerator / (p1 - p0) ** 2 + 0.999999999)


if __name__ == "__main__":
    for p0, delta in [(0.80, 0.05), (0.80, 0.03), (0.90, 0.03), (0.90, 0.02)]:
        print(p0, delta, required_n_per_group(p0, delta))

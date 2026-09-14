from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping


class HealthState(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


class IntegrityState(str, Enum):
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class MaintainerObservation:
    component: str
    health: HealthState
    integrity: IntegrityState
    version: str
    dependency_ok: bool
    lifecycle_ok: bool


@dataclass(frozen=True)
class MaintenanceDecision:
    action: str
    component: str
    reason: str


class SelfMaintainer:
    """DEE protection fabric: observe, isolate, recover, verify.

    This component is deliberately prohibited from mutating authoritative
    financial or asset truth. It returns decisions for an external controller.
    """

    def __init__(self, probes: Mapping[str, Callable[[], MaintainerObservation]]):
        self._probes = dict(probes)

    def inspect(self, component: str) -> MaintainerObservation:
        probe = self._probes.get(component)
        if probe is None:
            return MaintainerObservation(component, HealthState.FAILED, IntegrityState.UNKNOWN, "unknown", False, False)
        observation = probe()
        if not isinstance(observation, MaintainerObservation):
            raise TypeError("maintainer probe must return MaintainerObservation")
        return observation

    def decide(self, observation: MaintainerObservation) -> MaintenanceDecision:
        if observation.integrity != IntegrityState.VERIFIED:
            return MaintenanceDecision("ISOLATE", observation.component, "integrity-not-verified")
        if observation.health == HealthState.FAILED:
            return MaintenanceDecision("RECOVER", observation.component, "health-failed")
        if not observation.dependency_ok:
            return MaintenanceDecision("ISOLATE", observation.component, "dependency-failed")
        if not observation.lifecycle_ok:
            return MaintenanceDecision("RECOVER", observation.component, "lifecycle-invalid")
        return MaintenanceDecision("NONE", observation.component, "healthy")

    def inspect_and_decide(self, component: str) -> MaintenanceDecision:
        return self.decide(self.inspect(component))


__all__ = ["HealthState", "IntegrityState", "MaintainerObservation", "MaintenanceDecision", "SelfMaintainer"]

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from architecture.contracts import BoundaryRequest, BoundaryResponse


@dataclass(frozen=True)
class ServiceDefinition:
    name: str
    handler: Callable[[BoundaryRequest], Mapping[str, Any] | BoundaryResponse]


class ServiceCenter:
    """I2B Connection Gateway-ийн бизнес үйлчилгээний төв.

    ServiceCenter нь хөдөлгөөний engine биш. NEF/GerChain-ийн дотоод
    authoritative state-ийг өөртөө хадгалахгүй; зөвшөөрөгдсөн service handler
    руу л хүсэлтийг дамжуулна.
    """

    def __init__(self) -> None:
        self._services: dict[str, ServiceDefinition] = {}

    def register(self, name: str, handler: Callable[[BoundaryRequest], Mapping[str, Any] | BoundaryResponse]) -> None:
        if not name:
            raise ValueError("service name is required")
        if name in self._services:
            raise ValueError(f"service already registered: {name}")
        self._services[name] = ServiceDefinition(name=name, handler=handler)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._services))

    def dispatch(self, request: BoundaryRequest) -> BoundaryResponse:
        service = self._services.get(request.activity)
        if service is None:
            return BoundaryResponse(
                accepted=False,
                activity=request.activity,
                correlation_id=request.correlation_id,
                reason=f"Service not registered: {request.activity}",
            )
        result = service.handler(request)
        if isinstance(result, BoundaryResponse):
            return result
        return BoundaryResponse(
            accepted=True,
            activity=request.activity,
            correlation_id=request.correlation_id,
            data=dict(result),
        )


class I2BConnectionGateway:
    """I2B-ийн нэг цэгийн холболт: ServiceCenter + actor connectors."""

    def __init__(self, *, service_center: ServiceCenter, connector: Any | None = None) -> None:
        self.service_center = service_center
        self.connector = connector

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        if request.activity in self.service_center.names():
            return self.service_center.dispatch(request)
        if self.connector is not None:
            return self.connector.handle(request)
        return BoundaryResponse(
            accepted=False,
            activity=request.activity,
            correlation_id=request.correlation_id,
            reason="No service or connector registered for activity",
        )


__all__ = ["ServiceDefinition", "ServiceCenter", "I2BConnectionGateway"]

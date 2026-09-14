from __future__ import annotations

from architecture.boundary_adapters import I2BToEXIMBoundaryAdapter
from architecture.contracts import BoundaryRequest, BoundaryResponse
from services.exim_gateway import EXIMGateway
from services.i2b_service_center import ServiceCenter
from apps.shuud.service import SHUUDService


class SHUUDEximFlow:
    """SHUUD -> I2B Service Center -> I2B/EXIM Adapter -> EXIM."""

    def __init__(
        self,
        *,
        exim: EXIMGateway,
        service_center: ServiceCenter,
        i2b_to_exim: I2BToEXIMBoundaryAdapter | None = None,
    ) -> None:
        self.exim = exim
        self.service_center = service_center
        self.i2b_to_exim = i2b_to_exim or I2BToEXIMBoundaryAdapter(exim)

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        local = SHUUDService().handle(request)
        if not local.accepted:
            return local
        service = self.service_center.dispatch(request)
        if not service.accepted:
            return service
        return self.i2b_to_exim.handle(request)


__all__ = ["SHUUDEximFlow"]

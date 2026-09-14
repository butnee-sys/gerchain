from __future__ import annotations

from architecture.contracts import BoundaryRequest, BoundaryResponse
from services.exim_gateway import EXIMGateway
from services.i2b_service_center import ServiceCenter
from services.shuud_service import SHUUDService


class SHUUDEximFlow:
    """Compose SHUUD -> I2B Service Center -> EXIM without bypassing boundaries."""

    def __init__(self, *, exim: EXIMGateway, service_center: ServiceCenter) -> None:
        self.exim = exim
        self.service_center = service_center

    def handle(self, request: BoundaryRequest) -> BoundaryResponse:
        local = SHUUDService().handle(request)
        if not local.accepted:
            return local
        return self.exim.handle(request)


__all__ = ["SHUUDEximFlow"]

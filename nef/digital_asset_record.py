from __future__ import annotations

from typing import Any

from .contracts import Asset, DigitalAssetRecord


class DigitalAssetRecordEngine:
    def create(
        self,
        asset: Asset,
        data: dict[str, Any],
        evidence_ids: list[str] | None = None,
    ) -> DigitalAssetRecord:
        version = (
            1
            if asset.digital_record is None
            else asset.digital_record.version + 1
        )

        record = DigitalAssetRecord(
            record_id=f"{asset.asset_id}:DAR:{version}",
            version=version,
            data=dict(data),
            evidence_ids=list(evidence_ids or []),
        )

        asset.digital_record = record
        asset.touch()

        return record

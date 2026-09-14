from __future__ import annotations

from threading import RLock

from .contracts import Asset


class AssetAlreadyExistsError(ValueError):
    pass


class AssetNotFoundError(KeyError):
    pass


class AssetRegistryEngine:
    """
    Domain-level asset registry scaffold.

    Production authoritative persistence must be backed by
    transactional storage and database constraints.
    """

    def __init__(self) -> None:
        self._assets: dict[str, Asset] = {}
        self._lock = RLock()

    def register(self, asset: Asset) -> Asset:
        with self._lock:
            if asset.asset_id in self._assets:
                raise AssetAlreadyExistsError(asset.asset_id)

            self._assets[asset.asset_id] = asset
            return asset

    def get(self, asset_id: str) -> Asset:
        with self._lock:
            try:
                return self._assets[asset_id]
            except KeyError as exc:
                raise AssetNotFoundError(asset_id) from exc

    def exists(self, asset_id: str) -> bool:
        with self._lock:
            return asset_id in self._assets

    def count(self) -> int:
        with self._lock:
            return len(self._assets)

from typing import Dict, List

from app.models.schemas import Asset


class AssetStore:
    def __init__(self) -> None:
        self._assets: Dict[str, Asset] = {}

    @staticmethod
    def _key(symbol: str) -> str:
        return symbol.strip().upper()

    def list(self) -> List[Asset]:
        return list(self._assets.values())

    def add(self, asset: Asset) -> Asset:
        normalized = Asset(symbol=self._key(asset.symbol), type=asset.type)
        self._assets[self._key(asset.symbol)] = normalized
        return normalized

    def remove(self, symbol: str) -> bool:
        key = self._key(symbol)
        if key in self._assets:
            del self._assets[key]
            return True
        return False


asset_store = AssetStore()

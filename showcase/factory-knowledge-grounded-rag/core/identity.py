"""
Asset Identity and Hierarchy Management for Factory Knowledge Base.
"""

from typing import Dict, List, Optional
from core.schema import Asset


class AssetRegistry:
    """
    Registry for canonical physical assets and components.
    Provides hierarchical navigation (line -> machine -> subsystem -> component).
    """

    def __init__(self) -> None:
        self._assets: Dict[str, Asset] = {}
        self._children_index: Dict[str, List[str]] = {}

    def register_asset(self, asset: Asset) -> None:
        """Register or update an asset."""
        self._assets[asset.asset_id] = asset
        if asset.parent_asset_id:
            children = self._children_index.setdefault(asset.parent_asset_id, [])
            if asset.asset_id not in children:
                children.append(asset.asset_id)

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        """Lookup asset by canonical ID."""
        return self._assets.get(asset_id)

    def get_children(self, parent_asset_id: str) -> List[Asset]:
        """Return immediate children assets."""
        child_ids = self._children_index.get(parent_asset_id, [])
        return [self._assets[cid] for cid in child_ids if cid in self._assets]

    def get_ancestors(self, asset_id: str) -> List[Asset]:
        """Return ancestor chain up to the root asset."""
        ancestors: List[Asset] = []
        curr = self.get_asset(asset_id)
        while curr and curr.parent_asset_id:
            parent = self.get_asset(curr.parent_asset_id)
            if not parent:
                break
            ancestors.append(parent)
            curr = parent
        return ancestors

    def list_all(self) -> List[Asset]:
        """List all registered assets."""
        return list(self._assets.values())

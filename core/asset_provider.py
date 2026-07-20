from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class AssetProvider(ABC):
    """
    Abstract Base Class for Asset Providers.
    Defines the contract for fetching videos and music.
    """
    @abstractmethod
    def get_video(self, category: str) -> Optional[str]:
        """Fetch or return a valid video path for a category."""
        pass

    @abstractmethod
    def get_music(self, category: str) -> Optional[str]:
        """Fetch or return a valid music path for a category."""
        pass

    @abstractmethod
    def ensure_assets(self) -> Dict[str, Any]:
        """Ensure minimum assets are available (e.g. 10 per category)."""
        pass

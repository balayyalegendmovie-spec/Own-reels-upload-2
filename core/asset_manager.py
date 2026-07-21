import logging
from typing import Dict, Any

from core.config import ASSET_MODE
from visual.pexels_provider import PexelsProvider

logger = logging.getLogger(__name__)

class AssetManager:
    """
    Facade for managing assets.
    """
    def __init__(self):
        self.provider = PexelsProvider()
        logger.info("AssetManager initialized in PRODUCTION mode.")

    def ensure_assets(self) -> Dict[str, Any]:
        """Ensure the pipeline has all required media before generation starts."""
        logger.info("AssetManager: Ensuring required assets are available...")
        stats = self.provider.ensure_assets()
        logger.info(f"AssetManager: Asset check complete. Stats: {stats}")
        return stats

    def get_video(self, category: str) -> str:
        """Get a video for a category, utilizing the selected provider."""
        return self.provider.get_video(category)

    def get_music(self, category: str) -> str:
        """Get music for a category, utilizing the selected provider."""
        return self.provider.get_music(category)

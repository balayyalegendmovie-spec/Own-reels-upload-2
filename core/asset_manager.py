import logging
from typing import Dict, Any

from core.config import ASSET_MODE
from generated_asset_provider import GeneratedAssetProvider
from visual.pexels_provider import PexelsProvider

logger = logging.getLogger(__name__)

class AssetManager:
    """
    Facade for managing assets. Selects the appropriate provider based on ASSET_MODE.
    """
    def __init__(self):
        self.mode = ASSET_MODE
        if self.mode == "development":
            self.provider = GeneratedAssetProvider()
            logger.info("AssetManager initialized in DEVELOPMENT mode.")
        elif self.mode == "production":
            self.provider = PexelsProvider()
            logger.info("AssetManager initialized in PRODUCTION mode.")
        else:
            logger.warning(f"Unknown ASSET_MODE '{self.mode}'. Falling back to development.")
            self.provider = GeneratedAssetProvider()

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

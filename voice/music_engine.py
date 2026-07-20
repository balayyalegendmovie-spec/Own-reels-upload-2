import os
import random
import logging
from typing import Optional
from pathlib import Path
from core.config import MUSIC_DIR

logger = logging.getLogger(__name__)

class MusicEngine:
    def __init__(self, history_manager, asset_manager):
        self.history_manager = history_manager
        self.asset_manager = asset_manager

    def select_music(self, emotion: str) -> Optional[str]:
        """Select a background music file based on emotion and history."""
        emotion = emotion.lower()
        # Default mapping
        category = emotion
        category_dir = MUSIC_DIR / category
        
        if not category_dir.exists() or not category_dir.is_dir():
            logger.warning(f"Music category directory not found: {category_dir}")
            # try to fallback
            categories = [d for d in MUSIC_DIR.iterdir() if d.is_dir()]
            if not categories:
                return None
            category_dir = random.choice(categories)
            category = category_dir.name

        selected_track = None
        for _ in range(10):
            t = self.asset_manager.get_music(category)
            if not t:
                break
            if not self.history_manager.is_music_recently_used(str(t)):
                selected_track = t
                break
                
        if not selected_track:
            selected_track = self.asset_manager.get_music(category)
            
        if selected_track:
            self.history_manager.add_music_usage(str(selected_track))
        return str(selected_track) if selected_track else None

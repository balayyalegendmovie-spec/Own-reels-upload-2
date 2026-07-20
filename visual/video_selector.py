import os
import random
import logging
from typing import Optional
from pathlib import Path
from core.config import VIDEOS_DIR

logger = logging.getLogger(__name__)

class VideoSelector:
    def __init__(self, history_manager, asset_manager):
        self.history_manager = history_manager
        self.asset_manager = asset_manager

    def get_category_for_emotion(self, emotion: str) -> str:
        """Fallback map story emotion to video category."""
        emotion = emotion.lower()
        if emotion == "sad":
            return "rain"
        elif emotion == "peace":
            return random.choice(["forest", "ocean"])
        elif emotion == "motivation":
            return random.choice(["sunset", "city"])
        else:
            return random.choice(["forest", "ocean", "sunset", "city", "rain"])

    def select_multi_scene_videos(self, broll_keywords: dict, emotion: str) -> dict:
        """
        Selects or downloads a specific video for each scene in the story.
        Returns a dictionary mapping section name to video path.
        """
        selected_videos = {}
        fallback_category = self.get_category_for_emotion(emotion)
        
        sections = ["hook", "story", "emotional_payoff", "cta"]
        
        for section in sections:
            keyword = broll_keywords.get(section, "")
            
            video_path = None
            if keyword:
                # 1. Try to download from Pexels using the keyword directly
                # Sanitize keyword for filename
                safe_keyword = "".join([c for c in keyword if c.isalnum() or c == ' ']).strip().replace(' ', '_')
                
                # Make a dynamic directory for keywords or just save to a "dynamic" folder
                dynamic_dir = VIDEOS_DIR / "dynamic"
                dynamic_dir.mkdir(parents=True, exist_ok=True)
                
                # We append random id to avoid conflicts
                import uuid
                filename = str(dynamic_dir / f"{safe_keyword}_{uuid.uuid4().hex[:6]}.mp4")
                
                if hasattr(self.asset_manager.provider, "search_and_download_video"):
                    success = self.asset_manager.provider.search_and_download_video(keyword, filename)
                    if success and os.path.exists(filename):
                        video_path = filename
                        
            # 2. Fallback to existing videos in category if download failed or no keyword
            if not video_path:
                for _ in range(5):
                    v = self.asset_manager.get_video(fallback_category)
                    if v and not self.history_manager.is_video_recently_used(str(v)):
                        video_path = str(v)
                        break
                        
                if not video_path:
                    v = self.asset_manager.get_video(fallback_category)
                    if v:
                        video_path = str(v)
                        
            if video_path:
                self.history_manager.add_video_usage(video_path)
                selected_videos[section] = video_path
                
        return selected_videos

    def select_video(self, emotion: str) -> Optional[str]:
        """Legacy selection logic. Left for compatibility if needed."""
        category = self.get_category_for_emotion(emotion)
        category_dir = VIDEOS_DIR / category
        
        if not category_dir.exists() or not category_dir.is_dir():
            logger.warning(f"Category directory not found: {category_dir}")
            categories = [d for d in VIDEOS_DIR.iterdir() if d.is_dir()]
            if not categories:
                return None
            category_dir = random.choice(categories)

        selected_video = None
        for _ in range(10):
            v = self.asset_manager.get_video(category)
            if not v:
                break
            if not self.history_manager.is_video_recently_used(str(v)):
                selected_video = v
                break
                
        if not selected_video:
            selected_video = self.asset_manager.get_video(category)
            
        if selected_video:
            self.history_manager.add_video_usage(str(selected_video))
        return str(selected_video) if selected_video else None

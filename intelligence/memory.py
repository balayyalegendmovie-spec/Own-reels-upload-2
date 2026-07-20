import json
import logging
import datetime
from pathlib import Path
from typing import List, Dict, Any
from core.config import BASE_DIR, HISTORY_FILE

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self):
        self.history_db_file = BASE_DIR / "history_db.json"
        self.fallback_file = HISTORY_FILE
        self.history = self.load_history()

    def load_history(self) -> Dict[str, Any]:
        """Load history from JSON file or return default structure."""
        file_to_load = self.history_db_file
        if not file_to_load.exists() and self.fallback_file.exists():
            file_to_load = self.fallback_file
            
        if file_to_load.exists():
            try:
                with open(file_to_load, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure stories_used is a list
                    if "stories_used" not in data:
                        data["stories_used"] = []
                    return data
            except json.JSONDecodeError:
                logger.warning(f"History file {file_to_load} is corrupted. Creating a new one.")
                
        return {
            "videos_used": [],
            "music_used": [],
            "stories_used": []
        }

    def save_history(self) -> None:
        """Save current history to JSON file."""
        with open(self.history_db_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=4, ensure_ascii=False)

    def is_video_recently_used(self, video_path: str, recent_count: int = 10) -> bool:
        """Check if a video was used recently."""
        recent = self.history.get("videos_used", [])[-recent_count:]
        return video_path in recent

    def add_video_usage(self, video_path: str) -> None:
        """Record usage of a video."""
        if "videos_used" not in self.history:
            self.history["videos_used"] = []
        self.history["videos_used"].append(video_path)
        self.save_history()

    def is_music_recently_used(self, music_path: str, recent_count: int = 10) -> bool:
        """Check if music was used in the last `recent_count` reels."""
        recent = self.history.get("music_used", [])[-recent_count:]
        return music_path in recent

    def add_music_usage(self, music_path: str) -> None:
        """Record usage of a music track."""
        if "music_used" not in self.history:
            self.history["music_used"] = []
        self.history["music_used"].append(music_path)
        self.save_history()

    def add_story_usage(self, story_dict: Dict[str, Any]) -> None:
        """Record usage of a story."""
        if "stories_used" not in self.history:
            self.history["stories_used"] = []
        
        story_dict["timestamp"] = datetime.datetime.now().isoformat()
        self.history["stories_used"].append(story_dict)
        self.save_history()
        
    def is_idea_too_similar(self, hook: str, theme: str) -> bool:
        """Check if the idea overlaps with the last 20 stories."""
        stories = self.history.get("stories_used", [])
        recent_stories = stories[-20:]
        
        hook_words = set(hook.lower().split()) if hook else set()
        theme_words = set(theme.lower().split()) if theme else set()
        
        for story in recent_stories:
            if not isinstance(story, dict):
                # Handle old history format which was just strings
                continue
                
            past_hook = story.get("hook", "")
            past_theme = story.get("theme", "")
            
            past_hook_words = set(past_hook.lower().split()) if past_hook else set()
            past_theme_words = set(past_theme.lower().split()) if past_theme else set()
            
            # Simple word overlap similarity check
            if hook_words and past_hook_words:
                hook_overlap = len(hook_words.intersection(past_hook_words))
                if hook_overlap / len(hook_words) > 0.6:  # 60% overlap in hook
                    return True
                    
            if theme_words and past_theme_words:
                theme_overlap = len(theme_words.intersection(past_theme_words))
                if theme_overlap / len(theme_words) > 0.7:  # 70% overlap in theme
                    return True
                    
        return False

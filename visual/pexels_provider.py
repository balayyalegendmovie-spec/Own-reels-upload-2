import os
import requests
import logging
import random
from typing import Dict, Any, Optional
from pathlib import Path

from core.asset_provider import AssetProvider
from core.config import VIDEOS_DIR, MUSIC_DIR, PEXELS_API_KEY, JAMENDO_CLIENT_ID

logger = logging.getLogger(__name__)

class PexelsProvider(AssetProvider):
    """
    Production Asset Provider: Downloads real high-quality videos 
    from Pexels. Jamendo provides Audio.
    """
    def __init__(self):
        self.video_categories = ["rain", "forest", "ocean", "sunset", "city", "mountains", "study"]
        self.music_categories = ["emotional", "motivation", "peaceful"]
        self.min_assets = 10
        self.metadata = {"videos": {}, "music": {}}

    def _download_pexels_video(self, category: str, filepath: str):
        """Search and download a vertical video from Pexels API."""
        if not PEXELS_API_KEY:
            logger.warning("No PEXELS_API_KEY provided.")
            return False
            
        try:
            url = f"https://api.pexels.com/videos/search?query={category}&orientation=portrait&per_page=15"
            headers = {"Authorization": PEXELS_API_KEY}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            videos = data.get("videos", [])
            if not videos:
                logger.warning(f"No Pexels videos found for category: {category}")
                return False
                
            video = random.choice(videos)
            
            # Find the best quality mp4 link
            video_files = video.get("video_files", [])
            
            # Sort by quality
            best_video = None
            for vf in sorted(video_files, key=lambda x: x.get('width', 0) * x.get('height', 0), reverse=True):
                if vf.get("file_type") == "video/mp4" and vf.get("width", 0) <= 1080:  # Avoid 4K for speed if possible
                    best_video = vf
                    break
            
            if not best_video:
                best_video = video_files[0] if video_files else None
                
            if not best_video or not best_video.get("link"):
                return False
                
            video_url = best_video["link"]
            logger.info(f"Downloading Pexels video for {category}: {video_url}")
            
            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
            self.metadata["videos"][filepath] = {"quality": "external", "category": category, "source": "pexels"}
            return True
        except Exception as e:
            logger.error(f"Failed to download video from Pexels: {e}")
            return False

    def search_and_download_video(self, keyword: str, filepath: str) -> bool:
        """Search and download a specific vertical HD video from Pexels API based on dynamic keyword."""
        if not PEXELS_API_KEY:
            logger.warning("No PEXELS_API_KEY provided.")
            return False
            
        try:
            url = f"https://api.pexels.com/videos/search?query={keyword}&orientation=portrait&per_page=15"
            headers = {"Authorization": PEXELS_API_KEY}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            videos = data.get("videos", [])
            if not videos:
                logger.warning(f"No Pexels videos found for keyword: {keyword}")
                return False
                
            video = random.choice(videos[:5]) # Pick from top 5 for relevance
            
            # Find the best quality mp4 link
            video_files = video.get("video_files", [])
            
            best_video = None
            # Find a 1080p video (width <= 1080) to avoid 4K memory crashes, must be portrait
            for vf in sorted(video_files, key=lambda x: x.get('width', 0) * x.get('height', 0), reverse=True):
                if vf.get("file_type") == "video/mp4" and vf.get("width", 0) <= 1080 and vf.get("width", 0) < vf.get("height", 0):
                    best_video = vf
                    break
            
            if not best_video:
                best_video = video_files[0] if video_files else None
                
            if not best_video or not best_video.get("link"):
                return False
                
            video_url = best_video["link"]
            logger.info(f"Downloading Pexels video for '{keyword}': {video_url}")
            
            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
            self.metadata["videos"][filepath] = {"quality": "external", "keyword": keyword, "source": "pexels"}
            return True
        except Exception as e:
            logger.error(f"Failed to download video from Pexels for '{keyword}': {e}")
            return False

    def _download_jamendo_music(self, filepath: str, category: str):
        """Download real royalty-free music from Jamendo."""
        if not JAMENDO_CLIENT_ID:
            logger.warning("No JAMENDO_CLIENT_ID provided.")
            return False
            
        # Map our categories to Jamendo tags
        tag_map = {
            "peaceful": "ambient,relaxing",
            "motivation": "epic,cinematic",
            "emotional": "sad,piano,cinematic"
        }
        tags = tag_map.get(category, "background")
        
        try:
            url = f"https://api.jamendo.com/v3.0/tracks/?client_id={JAMENDO_CLIENT_ID}&format=json&limit=15&tags={tags}&include=musicinfo"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            if not results:
                logger.warning(f"No Jamendo music found for category: {category}")
                return False
                
            track = random.choice(results)
            audio_url = track.get("audiodownload")
            if not audio_url:
                # Fallback to audio (streaming link) if audiodownload is not available
                audio_url = track.get("audio")
                
            if not audio_url:
                return False
                
            logger.info(f"Downloading Jamendo music for {category}: {track.get('name')} by {track.get('artist_name')}")
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            with requests.get(audio_url, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
            self.metadata["music"][filepath] = {"quality": "external", "category": category, "source": "jamendo", "title": track.get("name")}
            return True
        except Exception as e:
            logger.error(f"Failed to download Jamendo music: {e}")
            return False

    def ensure_assets(self) -> Dict[str, Any]:
        """Verify minimum asset count. Fetch from APIs if needed."""
        logger.info("PexelsProvider: Ensuring assets via Pexels...")
        stats = {"videos_downloaded": 0, "music_generated": 0}
        
        # Check videos
        for cat in self.video_categories:
            cat_dir = VIDEOS_DIR / cat
            cat_dir.mkdir(parents=True, exist_ok=True)
            existing = [f for f in cat_dir.iterdir() if f.is_file() and f.suffix in ['.mp4']]
            if len(existing) < self.min_assets:
                for i in range(self.min_assets - len(existing)):
                    filepath = str(cat_dir / f"pexels_{cat}_{len(existing)+i}.mp4")
                    if self._download_pexels_video(cat, filepath):
                        stats["videos_downloaded"] += 1

        # Check music
        for cat in self.music_categories:
            cat_dir = MUSIC_DIR / cat
            cat_dir.mkdir(parents=True, exist_ok=True)
            existing = [f for f in cat_dir.iterdir() if f.is_file() and f.suffix in ['.mp3']]
            if len(existing) < self.min_assets:
                for i in range(self.min_assets - len(existing)):
                    filepath = str(cat_dir / f"jamendo_{cat}_{len(existing)+i}.mp3")
                    if self._download_jamendo_music(filepath, cat):
                        stats["music_generated"] += 1
                    
        return stats

    def get_video(self, category: str) -> Optional[str]:
        cat_dir = VIDEOS_DIR / category
        if cat_dir.exists():
            videos = [str(f) for f in cat_dir.iterdir() if f.suffix == '.mp4']
            if videos:
                return random.choice(videos)
        return None

    def get_music(self, category: str) -> Optional[str]:
        cat_dir = MUSIC_DIR / category
        if cat_dir.exists():
            music = [str(f) for f in cat_dir.iterdir() if f.suffix == '.mp3']
            if music:
                return random.choice(music)
        return None

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base Paths
from core.paths import BASE_DIR, INPUT_DIR, OUTPUT_DIR, ASSETS_DIR, MUSIC_DIR, VIDEOS_DIR
HISTORY_FILE = BASE_DIR / "database" / "history_db.json"

# API Keys and Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
IG_SESSION = os.getenv("IG_SESSION")

# Operating Mode
# "testing" -> Generates reel locally but does not upload to Instagram
# "production" -> Generates reel and uploads to Instagram if score >= 80
MODE = os.getenv("MODE", "testing").lower()

# Resolution & Output (Downscaled to 720p to prevent MemoryError)
REEL_WIDTH = 720
REEL_HEIGHT = 1280
REEL_FPS = 30
MIN_DURATION = 25
MAX_DURATION = 90

# Safe Zones (Instagram Reels UI)
SAFE_MARGIN_TOP = int(os.getenv("SAFE_MARGIN_TOP", "250"))
SAFE_MARGIN_BOTTOM = int(os.getenv("SAFE_MARGIN_BOTTOM", "450"))
SAFE_MARGIN_X = int(os.getenv("SAFE_MARGIN_X", "80"))

# Voice Settings
DEFAULT_VOICE = "te-IN-ShrutiNeural"

# Modes
ASSET_MODE = os.getenv("ASSET_MODE", "production") # 'development' or 'production'
RENDER_MODE = os.getenv("RENDER_MODE", "cinematic") # 'minimal' or 'cinematic'

# External API Keys
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "VH7Jg7XY2NzZ3N1spws2hq0mrf7f5vA5KzVWDsRBSnGQh0aHzwLZxWzm")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
JAMENDO_CLIENT_ID = os.getenv("JAMENDO_CLIENT_ID", "")

def ensure_directories():
    """Ensure all required directories exist."""
    dirs_to_create = [
        INPUT_DIR,
        OUTPUT_DIR,
        VIDEOS_DIR / "rain",
        VIDEOS_DIR / "forest",
        VIDEOS_DIR / "ocean",
        VIDEOS_DIR / "sunset",
        VIDEOS_DIR / "city",
        VIDEOS_DIR / "mountains",
        VIDEOS_DIR / "study",
        MUSIC_DIR / "emotional",
        MUSIC_DIR / "motivation",
        MUSIC_DIR / "peaceful",
    ]
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)

ensure_directories()

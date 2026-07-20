import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
DATABASE_DIR = BASE_DIR / "database"
ASSETS_DIR = BASE_DIR / "assets"
MUSIC_DIR = BASE_DIR / "music"
VIDEOS_DIR = BASE_DIR / "videos"

# Ensure all paths exist
for d in [INPUT_DIR, OUTPUT_DIR, DATABASE_DIR, ASSETS_DIR, MUSIC_DIR, VIDEOS_DIR]:
    d.mkdir(exist_ok=True)

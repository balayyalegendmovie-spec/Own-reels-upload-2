import os
import sys
import shutil
from pathlib import Path

def check_dependencies():
    print("Checking dependencies...")
    try:
        import moviepy
        import ffmpeg
        import edge_tts
        import PIL
        import cv2
        print("[OK] Python dependencies verified.")
    except ImportError as e:
        print(f"[ERROR] Missing Python dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

    if not shutil.which("ffmpeg"):
        print("[ERROR] FFmpeg not found in PATH.")
        print("Please install FFmpeg and add it to your system PATH.")
        sys.exit(1)
    else:
        print("[OK] FFmpeg verified.")

def setup_directories():
    base_dir = Path(__file__).parent.absolute()
    dirs = [
        "input",
        "output",
        "videos/rain",
        "videos/forest",
        "videos/ocean",
        "videos/sunset",
        "videos/city",
        "videos/mountains",
        "videos/study",
        "music/emotional",
        "music/motivation",
        "music/peaceful",
    ]
    for d in dirs:
        dir_path = base_dir / d
        dir_path.mkdir(parents=True, exist_ok=True)
    
    themes_file = base_dir / "input" / "themes.txt"
    if not themes_file.exists():
        with open(themes_file, "w", encoding="utf-8") as f:
            f.write("student motivation\nlife lesson\nemotional story\npeaceful nature\ncareer motivation\n")
            
    print("[OK] Directory structure verified.")

if __name__ == "__main__":
    print("Starting Telugu AI Reel Factory Setup...")
    setup_directories()
    check_dependencies()
    print("Setup complete! You can now run main.py")

# Telugu AI Reel Factory V6

A fully autonomous, cloud-ready AI factory that automatically generates, edits, scores, and uploads Telugu motivational and emotional short-form video reels to Instagram every day.

## Architecture

This project operates on a fully automated CI/CD pipeline using **GitHub Actions**.

1. **Idea Generation**: `input/content_queue.json` feeds topics.
2. **AI Story**: Google Gemini generates a highly engaging hook, story, and cinematic directions in Telugu script.
3. **Voice acting**: Edge TTS synthesizes emotional Telugu speech (`Shruti` neural voice).
4. **Cinematic Selection**: Automatically fetches royalty-free B-roll from Pexels and background music.
5. **Editing**: MoviePy stitches everything together with a 720p cinematic Hard-cut style.
6. **Subtitles**: HarfBuzz + Pillow shapes and renders flawless Telugu typography directly onto the video.
7. **Validation**: The internal AI validates Hook Length, Visual Matching, Audio Ducking, and Duration to generate a 0-100 Quality Score.
8. **Distribution**: If the score is >= 80, the reel is uploaded to Instagram using `instagrapi`.

## Setup (Local)

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Ensure FFmpeg is installed and added to your path.
4. Add your secrets to a `.env` file (see `.env.example`).
5. Run the pipeline locally:
```bash
python main.py
```

## Setup (GitHub Actions Automation)

To run this entirely in the cloud on auto-pilot:
1. Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions**
2. Add the following secrets:
   - `GEMINI_API_KEY`: Your Google Gemini API Key
   - `PEXELS_API_KEY`: Your Pexels API Key
   - `IG_SESSION`: Your extracted Instagram `sessionid` cookie value.
3. The pipeline will automatically run at 6:00 AM IST daily.

*Note: Do NOT upload `session.json`, `.env`, or API keys directly to the repository.*

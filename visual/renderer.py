"""
Reel Renderer V4

Combines cinematic gradient background + Pillow subtitle overlay + audio.
No more FFmpeg ASS subtitle burning.

Pipeline:
  1. Generate cinematic gradient background (numpy)
  2. Add slow zoom + light leak + minimal particles
  3. Overlay Pillow-rendered Telugu subtitles via MoviePy composite
  4. Mix voice + music audio
  5. Export final MP4
"""
import os
import logging
import numpy as np
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeAudioClip,
    CompositeVideoClip, VideoClip, concatenate_videoclips
)
import moviepy.video.fx.all as vfx
import moviepy.audio.fx.all as afx
from subtitles.subtitle_engine import SubtitleEngine
from subtitles.pillow_subtitle_renderer import PillowSubtitleRenderer
from core.config import REEL_WIDTH, REEL_HEIGHT, REEL_FPS, RENDER_MODE
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


def create_gradient_frame(t, duration, color1, color2, size):
    """Generate a cinematic gradient frame with light leak and particles."""
    w, h = size
    
    # 1. Vertical Gradient with slow drift
    y = np.linspace(0, 1, h)
    drift = (t / duration) * 0.2
    y = np.clip(y - drift, 0, 1)
    
    c1 = np.array(color1, dtype=np.float32)
    c2 = np.array(color2, dtype=np.float32)
    grad = c1 * (1 - y[:, None, None]) + c2 * y[:, None, None]
    grad = np.tile(grad, (1, w, 1))
    
    # 2. Cinematic Light Leak (Radial Glow)
    center_x = w * (0.2 + (t / duration) * 0.6)
    center_y = h * (0.1 + (t / duration) * 0.4)
    radius = w * 0.8
    
    y_grid, x_grid = np.ogrid[:h, :w]
    dist = np.sqrt((x_grid - center_x)**2 + (y_grid - center_y)**2)
    glow = np.clip(1.0 - (dist / radius)**1.5, 0, 1)
    
    glow_color = np.array([50, 40, 60], dtype=np.float32)
    grad += glow[:, :, None] * glow_color[None, None, :]
    
    # 3. Minimal Particles (subtle floating upwards)
    np.random.seed(42)
    num_particles = 40  # Reduced for subtlety
    px = np.random.randint(0, w, num_particles)
    py = np.random.randint(0, h * 2, num_particles)
    
    py_current = (py - int((t / duration) * h * 0.5)) % h
    
    for i in range(num_particles):
        cx, cy = px[i], py_current[i]
        # Draw a tiny 2x2 soft dot (smaller = more subtle)
        for dx in [0, 1]:
            for dy in [0, 1]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < w and 0 <= ny < h:
                    grad[ny, nx] = np.clip(grad[ny, nx] + 120, 0, 255)
    
    return np.clip(grad, 0, 255).astype(np.uint8)


class Renderer:
    def __init__(self):
        self.subtitle_engine = SubtitleEngine()
        self.subtitle_renderer = PillowSubtitleRenderer(REEL_WIDTH, REEL_HEIGHT)

    def render(self, video_paths: Dict[str, str], voice_path: str, music_path: str, vtt_path: str, 
               script: str, variation: Dict[str, Any], section_timings: Dict[str, Tuple[float, float]], output_path: str):
        """
        V4 Render Pipeline:
        Background + Pillow Subtitles + Audio -> Final Reel
        """
        logger.info(f"Starting V4 reel rendering in {RENDER_MODE.upper()} mode...")
        
        try:
            # 1. Load voice and measure exact duration
            voice_clip = AudioFileClip(voice_path)
            duration = voice_clip.duration
            logger.info(f"Voice duration: {duration:.1f}s — video will match exactly.")

            # 2. Parse VTT into structured subtitle chunks
            subtitle_chunks = self.subtitle_engine.parse_vtt(
                vtt_path, script, duration
            )
            logger.info(f"Parsed {len(subtitle_chunks)} subtitle chunks.")
            
            # 3. Create Pillow subtitle overlay clip
            subtitle_clip = self.subtitle_renderer.create_subtitle_clip(
                subtitle_chunks, duration
            )
                
            # 4. Mix audio
            music_clip = None
            if music_path and os.path.exists(music_path):
                music_clip = AudioFileClip(music_path)
                if music_clip.duration < duration:
                    music_clip = afx.audio_loop(music_clip, duration=duration)
                else:
                    music_clip = music_clip.subclip(0, duration)
                music_clip = music_clip.volumex(0.12)  # 12% volume
                
            if music_clip:
                final_audio = CompositeAudioClip([voice_clip, music_clip]).set_duration(duration)
            else:
                final_audio = voice_clip.set_duration(duration)
                
            # 5. Create background video
            if RENDER_MODE == "minimal":
                logger.info("Generating cinematic minimal gradient background.")
                emotion = variation.get("emotion", "peaceful").lower()
                
                # Style Presets
                if "emotional" in emotion or "sad" in emotion:
                    c1, c2 = [20, 25, 40], [10, 10, 20]  # Deep blue
                elif "motivation" in emotion or "inspire" in emotion:
                    c1, c2 = [40, 20, 20], [60, 40, 20]  # Warm orange
                else:  # peaceful
                    c1, c2 = [20, 40, 40], [15, 20, 30]  # Calm teal
                    
                bg_clip = VideoClip(
                    lambda t: create_gradient_frame(t, duration, c1, c2, (REEL_WIDTH, REEL_HEIGHT)),
                    duration=duration
                )
                
                # Apply slow zoom (1.0 to 1.08x — subtle)
                def zoom(t):
                    return 1.0 + 0.08 * (t / duration)
                
                bg_clip = bg_clip.resize(zoom)
                bg_clip = bg_clip.crop(
                    x_center=REEL_WIDTH/2, y_center=REEL_HEIGHT/2,
                    width=REEL_WIDTH, height=REEL_HEIGHT
                )
            else:
                # Cinematic multi-scene mode
                clips = []
                sections = ["hook", "story", "emotional_payoff", "cta"]
                
                # Make sure we cover the entire duration, even if timings have tiny gaps
                last_end = 0.0
                
                for i, section in enumerate(sections):
                    vid_path = video_paths.get(section)
                    timing = section_timings.get(section)
                    
                    if not vid_path or not timing:
                        continue
                        
                    start_t, end_t = timing
                    
                    # Ensure continuity (bridge any gaps caused by edge-tts silence)
                    if start_t > last_end:
                        start_t = last_end
                        
                    clip_dur = end_t - start_t
                    if clip_dur <= 0:
                        continue
                        
                    if i == len(sections) - 1:
                        # Last clip extends to full duration
                        clip_dur = duration - start_t
                    
                    try:
                        vc = VideoFileClip(vid_path)
                        if vc.duration < clip_dur:
                            vc = vfx.loop(vc, duration=clip_dur)
                        vc = vc.subclip(0, clip_dur)
                        
                        # Crop to 9:16
                        x_center = vc.size[0] / 2
                        y_center = vc.size[1] / 2
                        if vc.size[0] >= REEL_WIDTH and vc.size[1] >= REEL_HEIGHT:
                            vc = vc.crop(x_center=x_center, y_center=y_center, width=REEL_WIDTH, height=REEL_HEIGHT)
                        else:
                            vc = vc.resize(height=REEL_HEIGHT)
                            x_center = vc.size[0] / 2
                            vc = vc.crop(x_center=x_center, width=REEL_WIDTH)
                            
                        # Add crossfade unless it's the first clip
                        # Removed crossfadein to prevent MoviePy MemoryError
                        # if len(clips) > 0:
                        #     vc = vc.crossfadein(0.5)
                            
                        clips.append(vc)
                        last_end = start_t + clip_dur
                        
                    except Exception as e:
                        logger.error(f"Error loading clip {vid_path}: {e}")
                        
                if clips:
                    # Concatenate with hard cuts to prevent OOM
                    bg_clip = concatenate_videoclips(clips, method="chain")
                    
                    # If concatenation ends up slightly shorter or longer, force duration
                    if bg_clip.duration != duration:
                        bg_clip = bg_clip.set_duration(duration)
                else:
                    # Fallback to gradient if all clips failed
                    logger.warning("All clips failed loading, falling back to gradient.")
                    c1, c2 = [20, 25, 40], [10, 10, 20]
                    bg_clip = VideoClip(lambda t: create_gradient_frame(t, duration, c1, c2, (REEL_WIDTH, REEL_HEIGHT)), duration=duration)

            # 6. Composite: background + subtitle overlay
            final_video = CompositeVideoClip(
                [bg_clip, subtitle_clip],
                size=(REEL_WIDTH, REEL_HEIGHT)
            )
            final_video = final_video.set_audio(final_audio)
            final_video = final_video.set_duration(duration)
            
            # 7. Export
            logger.info(f"Exporting final reel to {output_path}")
            final_video.write_videofile(
                output_path,
                fps=REEL_FPS,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
                threads=1,
                logger=None
            )
            
            # Generate thumbnail at a good frame (e.g., 2.0s into the hook)
            thumbnail_path = output_path.replace(".mp4", "_thumb.jpg")
            try:
                final_video.save_frame(thumbnail_path, t=2.0)
                logger.info(f"Thumbnail saved to {thumbnail_path}")
            except Exception as e:
                logger.warning(f"Failed to generate thumbnail: {e}")
            
            # Cleanup
            voice_clip.close()
            if music_clip:
                music_clip.close()
            bg_clip.close()
            
            logger.info("V4 Reel rendering complete!")
            
        except Exception as e:
            logger.error(f"Failed to render reel: {e}", exc_info=True)
            raise

    def render_preview(self, video_paths: Dict[str, str], voice_path: str, music_path: str,
                       vtt_path: str, script: str, variation: Dict[str, Any], section_timings: Dict[str, Tuple[float, float]],
                       output_path: str, preview_duration: float = 5.0):
        """
        Generate a 5-second preview clip for quick validation.
        """
        logger.info(f"Generating {preview_duration}s preview...")
        
        try:
            voice_clip = AudioFileClip(voice_path)
            duration = min(preview_duration, voice_clip.duration)
            
            subtitle_chunks = self.subtitle_engine.parse_vtt(vtt_path, script, voice_clip.duration)
            # Filter chunks to only those within preview window
            preview_chunks = [c for c in subtitle_chunks if c['start'] < duration]
            
            subtitle_clip = self.subtitle_renderer.create_subtitle_clip(preview_chunks, duration)
            
            emotion = variation.get("emotion", "peaceful").lower()
            
            # Use the hook video if available, else first video, else gradient
            bg_clip = None
            hook_video = video_paths.get("hook")
            if not hook_video and video_paths:
                hook_video = list(video_paths.values())[0]
                
            if hook_video:
                try:
                    bg_clip = VideoFileClip(hook_video).subclip(0, duration)
                    x_center = bg_clip.size[0] / 2
                    y_center = bg_clip.size[1] / 2
                    if bg_clip.size[0] >= REEL_WIDTH and bg_clip.size[1] >= REEL_HEIGHT:
                        bg_clip = bg_clip.crop(x_center=x_center, y_center=y_center, width=REEL_WIDTH, height=REEL_HEIGHT)
                    else:
                        bg_clip = bg_clip.resize(height=REEL_HEIGHT)
                        x_center = bg_clip.size[0] / 2
                        bg_clip = bg_clip.crop(x_center=x_center, width=REEL_WIDTH)
                except Exception as e:
                    logger.warning(f"Preview video failed to load, falling back to gradient: {e}")
                    bg_clip = None
            
            if not bg_clip:
                if "emotional" in emotion or "sad" in emotion:
                    c1, c2 = [20, 25, 40], [10, 10, 20]
                elif "motivation" in emotion or "inspire" in emotion:
                    c1, c2 = [40, 20, 20], [60, 40, 20]
                else:
                    c1, c2 = [20, 40, 40], [15, 20, 30]
                    
                bg_clip = VideoClip(
                    lambda t: create_gradient_frame(t, duration, c1, c2, (REEL_WIDTH, REEL_HEIGHT)),
                    duration=duration
                )
            
            final_video = CompositeVideoClip(
                [bg_clip, subtitle_clip],
                size=(REEL_WIDTH, REEL_HEIGHT)
            )
            
            # Use only voice for preview
            preview_audio = voice_clip.subclip(0, duration)
            final_video = final_video.set_audio(preview_audio)
            final_video = final_video.set_duration(duration)
            
            final_video.write_videofile(
                output_path,
                fps=REEL_FPS,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio-preview.m4a",
                remove_temp=True,
                threads=1,
                logger=None
            )
            
            voice_clip.close()
            bg_clip.close()
            
            logger.info(f"Preview saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to render preview: {e}", exc_info=True)
            raise

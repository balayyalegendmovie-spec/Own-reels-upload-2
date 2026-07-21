import os
import json
import logging
import uuid
import datetime
import traceback
from pathlib import Path

from core.config import MODE
from core.paths import INPUT_DIR, OUTPUT_DIR, DATABASE_DIR
from intelligence.memory import MemoryManager
from story_engine.gemini_story import StoryEngine
from voice.voice_director import VoiceDirector
from voice.tts_engine import TTSEngine
from voice.audio_processor import AudioProcessor
from visual.video_selector import VideoSelector
from voice.music_engine import MusicEngine
from intelligence.variation_engine import VariationEngine
from visual.renderer import Renderer
from core.asset_manager import AssetManager
from subtitles.font_validator import FontValidator
from story_engine.hook_optimizer import HookOptimizer
from subtitles.text_normalizer import TextNormalizer
from subtitles.word_timing_engine import WordTimingEngine
from intelligence.quality_validator import QualityValidator
from intelligence.quality_score import QualityScore
from instagram.uploader import InstagramUploader

logger = logging.getLogger(__name__)

class Pipeline:
    def __init__(self):
        self.history_manager = MemoryManager()
        self.asset_manager = AssetManager()
        self.story_engine = StoryEngine(self.history_manager)
        self.voice_director = VoiceDirector()
        self.tts_engine = TTSEngine()
        self.audio_processor = AudioProcessor()
        self.video_selector = VideoSelector(self.history_manager, self.asset_manager)
        self.music_engine = MusicEngine(self.history_manager, self.asset_manager)
        self.variation_engine = VariationEngine()
        self.reel_renderer = Renderer()
        self.hook_optimizer = HookOptimizer()
        self.quality_scorer = QualityScore()
        self.word_timing_engine = WordTimingEngine()
        self.uploader = InstagramUploader()
        
        try:
            from subtitles.telugu_text_cleaner import TeluguTextCleaner
            self.text_cleaner = TeluguTextCleaner()
        except Exception:
            self.text_cleaner = None

    def run(self):
        logger.info("Starting Telugu AI Reel Factory V6 Pipeline...")
        
        font_validator = FontValidator()
        if not font_validator.validate():
            logger.error("FATAL: Telugu font validation FAILED. Cannot proceed.")
            return

        self.asset_manager.ensure_assets()
        
        queue_file = INPUT_DIR / "content_queue.json"
        if not queue_file.exists():
            logger.error(f"Content queue file not found: {queue_file}")
            return
            
        with open(queue_file, "r", encoding="utf-8") as f:
            queue = json.load(f)
            
        pending_tasks = [q for q in queue if q.get("status") == "pending"]
        
        # Infinite Content Engine: Refill queue if empty
        if not pending_tasks:
            logger.info("Content queue is empty! Auto-generating new topics via Gemini...")
            new_topics = self.story_engine.generate_new_topics(count=5)
            if new_topics:
                queue.extend(new_topics)
                pending_tasks = new_topics
                logger.info(f"Successfully brainstormed {len(new_topics)} new topics and added to queue.")
            else:
                logger.error("Failed to auto-generate new topics. Pipeline halting.")
                return
                
        if not pending_tasks:
            logger.info("No pending tasks in content queue despite auto-fill attempt.")
            return
            
        current_task = pending_tasks[0]
        theme = current_task.get("topic", "life lesson")
        
        logger.info(f"Selected Theme from Queue: {theme}")
        
        try:
            self._execute_pipeline(theme, current_task)
            
            # Update queue status
            current_task["status"] = "completed"
                
        except Exception as e:
            logger.error(f"Pipeline failed for {theme}: {e}", exc_info=True)
            self._log_error(current_task.get("id"), str(e), traceback.format_exc())
            current_task["status"] = "failed"
            
        # Update queue
        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=4)

    def _execute_pipeline(self, theme, task_config):
        MAX_REEL_RETRIES = 3
        for reel_attempt in range(MAX_REEL_RETRIES):
            logger.info(f"Reel generation attempt {reel_attempt + 1}/{MAX_REEL_RETRIES}")
            MAX_STORY_RETRIES = 3
            story_data = None
            # 1. Story Generation (with Retries)
            for attempt in range(MAX_STORY_RETRIES):
                logger.info(f"Story generation attempt {attempt + 1}/{MAX_STORY_RETRIES}")
                story_data = self.story_engine.generate_story(theme)
                if not story_data:
                    continue
                
                hook = story_data.get('hook', '')
                if self.history_manager.is_idea_too_similar(hook, theme):
                    logger.warning("Idea too similar. Regenerating...")
                    story_data = None
                    continue
                
                if not story_data.get('cta') or len(story_data.get('cta', '').strip()) < 5:
                    story_data = None
                    continue
                
                break
            
            if not story_data:
                raise Exception("Failed to generate a valid story after max retries.")
            
            if self.text_cleaner:
                for field in ['hook', 'story', 'emotional_payoff', 'lesson', 'cta', 'script']:
                    if field in story_data and story_data[field]:
                        story_data[field] = self.text_cleaner.clean(story_data[field])

            # 2. Voice Generation
            voice_config = self.voice_director.get_voice_config(story_data)
            raw_voice_path = str(OUTPUT_DIR / "raw_voice.mp3")
            timestamps_path = str(OUTPUT_DIR / "word_timestamps.json")
        
            _, boundary_events, section_timings = self.tts_engine.generate_segmented_voice(
                story_data, voice_config, raw_voice_path
            )
            self.word_timing_engine.estimate_word_timings(boundary_events, timestamps_path)
        
            from moviepy.editor import AudioFileClip
            voice_clip = AudioFileClip(raw_voice_path)
            duration = voice_clip.duration
            voice_clip.close()
        
            story_data["duration"] = duration
        
            # 3. Audio Processing
            final_voice_path = str(OUTPUT_DIR / "final_voice.mp3")
            self.audio_processor.humanize_voice(raw_voice_path, final_voice_path)

            # 4. Asset Selection
            emotion = story_data.get("emotion", "peaceful")
            broll_keywords = story_data.get("broll_keywords", {})
            video_paths = self.video_selector.select_multi_scene_videos(broll_keywords, emotion)
            music_path = self.music_engine.select_music(emotion)

            final_mixed_audio = final_voice_path
            has_music = False
            if music_path and os.path.exists(music_path):
                mixed_audio_path = str(OUTPUT_DIR / "final_mixed.mp3")
                try:
                    self.audio_processor.mix_with_ducking(final_voice_path, music_path, mixed_audio_path)
                    final_mixed_audio = mixed_audio_path
                    has_music = True
                except Exception as e:
                    logger.warning(f"Ducking failed: {e}")

            # 5. Render Video
            variation_config = self.variation_engine.get_variation_config()
            variation_config["duration"] = duration
            variation_config["emotion"] = emotion

            final_reel_path = str(OUTPUT_DIR / "final_reel.mp4")
            raw_vtt_path = str(OUTPUT_DIR / "word_timestamps.vtt")
        
            self.reel_renderer.render(
                video_paths=video_paths,
                voice_path=final_mixed_audio,
                music_path="",
                vtt_path=raw_vtt_path,
                script=story_data["script"],
                variation=variation_config,
                section_timings=section_timings,
                output_path=final_reel_path
            )
        
            # 6. Quality Check
            quality_score = self.quality_scorer.evaluate(story_data, duration, video_paths, has_music)

            if quality_score["score"] < 80:
                logger.warning(f"Quality score {quality_score['score']} < 80. Retrying reel generation...")
                if reel_attempt < MAX_REEL_RETRIES - 1:
                    continue
                else:
                    raise Exception(f"Failed to generate high-quality reel after {MAX_REEL_RETRIES} attempts.")

        
            # 7. Metadata and History
            gen_id = uuid.uuid4().hex[:8]
            metadata = {
                "generation_id": gen_id,
                "topic": theme,
                "quality_score": quality_score["score"]
            }
            meta_path = str(OUTPUT_DIR / f"metadata_{gen_id}.json")
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4)
            
            self.history_manager.add_story_usage({
                "hook": story_data.get("hook", ""),
                "theme": theme,
                "emotion": emotion
            })
        
            # 8. Upload
            if quality_score["score"] >= 80:
                if MODE == "production":
                    logger.info("Quality >= 80 and Mode=PRODUCTION. Initiating upload...")
                    if self.uploader.login():
                        ai_caption = story_data.get('caption', story_data.get('hook', ''))
                        ai_hashtags = story_data.get('hashtags', '#telugu #telugureels #motivation #trending')
                    
                        # Ensure hashtags aren't duplicated if the AI already included them in the caption
                        if ai_hashtags not in ai_caption:
                            caption = f"{ai_caption}\n\n{ai_hashtags}"
                        else:
                            caption = ai_caption
                        
                        thumb = final_reel_path.replace(".mp4", "_thumb.jpg")
                        self.uploader.upload_reel(final_reel_path, caption, thumb)
                else:
                    logger.info("Quality >= 80, but Mode=TESTING. Skipping upload.")
            else:
            
            break

    def _log_error(self, task_id, error_msg, trace):
        errors_file = DATABASE_DIR / "errors.json"
        errors = []
        if errors_file.exists():
            with open(errors_file, "r") as f:
                errors = json.load(f)
                
        errors.append({
            "task_id": task_id,
            "error": error_msg,
            "traceback": trace,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        with open(errors_file, "w") as f:
            json.dump(errors, f, indent=4)

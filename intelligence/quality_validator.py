import json
import logging
import subprocess
import os
import re
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class QualityValidator:
    """
    QualityValidator runs final checks before export on the generated video and audio assets.
    """
    def __init__(self, video_path: str, voice_path: str, vtt_path: str, story_data: Dict[str, Any]):
        self.video_path = video_path
        self.voice_path = voice_path
        self.vtt_path = vtt_path
        self.story_data = story_data
        
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        """Runs all validations and returns True if no critical errors were found."""
        self.errors.clear()
        self.warnings.clear()

        self._check_rendering_artifacts()
        self._check_ssml_tags()
        self._check_cta_exists()
        self._check_durations()

        if self.errors:
            logger.error(f"Quality Validation Failed with errors: {self.errors}")
            return False
        
        if self.warnings:
            logger.warning(f"Quality Validation finished with warnings: {self.warnings}")
            
        logger.info("Quality Validation passed successfully.")
        return True

    def _get_vtt_text(self) -> str:
        """Reads the VTT file and returns its content as a string."""
        if not os.path.exists(self.vtt_path):
            self.errors.append(f"VTT file not found: {self.vtt_path}")
            return ""
        try:
            with open(self.vtt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.errors.append(f"Failed to read VTT file: {e}")
            return ""

    def _check_rendering_artifacts(self):
        """
        Checks if Telugu characters rendered correctly (no ◌ - \u25CC) and
        if English words are readable (no broken glyphs - \uFFFD).
        """
        vtt_text = self._get_vtt_text()
        full_text = vtt_text + " " + str(self.story_data)
        
        if '\u25CC' in full_text:  # Dotted circle usually indicates broken conjuncts
            self.errors.append("Found broken Telugu characters (dotted circle ◌) in text.")
            
        if '\uFFFD' in full_text:  # Replacement character indicates broken glyphs/encoding
            self.errors.append("Found broken characters/glyphs () in text.")

    def _check_ssml_tags(self):
        """Checks that no <break or <speak SSML tags are in the final VTT/text."""
        vtt_text = self._get_vtt_text()
        
        # Check both the raw story script and the VTT
        script_text = self.story_data.get("script", "")
        
        if re.search(r'<break|<speak|</speak>', vtt_text, re.IGNORECASE):
            self.errors.append("Found unresolved SSML tags (<break or <speak) in VTT text.")
            
        if re.search(r'<break|<speak|</speak>', script_text, re.IGNORECASE):
            self.errors.append("Found unresolved SSML tags (<break or <speak) in story script.")

    def _check_cta_exists(self):
        """Checks if CTA exists in the story data."""
        cta = self.story_data.get("cta")
        if not cta or not str(cta).strip():
            self.errors.append("CTA is missing from story data.")

    def _get_duration(self, file_path: str) -> float:
        """Uses ffprobe to get the duration of a media file in seconds."""
        if not os.path.exists(file_path):
            self.errors.append(f"Media file not found: {file_path}")
            return 0.0
            
        try:
            cmd = [
                'ffprobe', 
                '-v', 'error', 
                '-show_entries', 'format=duration', 
                '-of', 'default=noprint_wrappers=1:nokey=1', 
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration_str = result.stdout.strip()
            if duration_str:
                return float(duration_str)
        except Exception as e:
            logger.warning(f"Could not get duration for {file_path} using ffprobe: {e}")
        return 0.0

    def _check_durations(self):
        """Checks if voice duration approximately equals video duration."""
        video_dur = self._get_duration(self.video_path)
        voice_dur = self._get_duration(self.voice_path)
        
        if video_dur > 0 and voice_dur > 0:
            diff = abs(video_dur - voice_dur)
            # Allow a small tolerance of 1 second for rounding differences
            if diff > 1.0:
                self.errors.append(f"Duration mismatch: Video ({video_dur:.2f}s) and Voice ({voice_dur:.2f}s) differ by {diff:.2f}s.")
        else:
            self.warnings.append("Could not verify durations (ffprobe might be missing or files invalid).")

    def get_report(self) -> Dict[str, Any]:
        """Returns a report of the validation."""
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings
        }

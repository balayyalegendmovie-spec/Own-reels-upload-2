import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class QualityScore:
    """
    Evaluates the quality of a generated reel before export.
    Returns a score and boolean pass/fail.
    """
    def __init__(self):
        self.min_passing_score = 80
        
    def evaluate(self, story_data: Dict[str, Any], duration: float, video_paths: Dict[str, str], has_music: bool) -> Dict[str, Any]:
        """
        Evaluate reel based on multiple factors.
        Max score is 100.
        
        Final score distribution:
        40% Content
        30% Visual
        20% Audio
        10% Technical
        """
        score = 0
        feedback = []
        
        # ==========================================
        # 1. Content (Max 40 points)
        # ==========================================
        content_score = 0
        hook = story_data.get("hook", "")
        if hook:
            words = len(hook.split())
            if 4 <= words <= 12:
                content_score += 15
            else:
                content_score += 5
                feedback.append("Hook length is suboptimal.")
        else:
            feedback.append("Missing hook.")
            
        if story_data.get("story") and story_data.get("emotional_payoff"):
            content_score += 15
        else:
            feedback.append("Missing story or emotional payoff.")
            
        if story_data.get("cta") and len(story_data.get("cta")) > 5:
            content_score += 10
        else:
            feedback.append("Missing CTA.")
            
        score += content_score
            
        # ==========================================
        # 2. Visual (Max 30 points)
        # ==========================================
        visual_score = 0
        sections = ["hook", "story", "emotional_payoff", "cta"]
        missing_videos = []
        for s in sections:
            if not video_paths.get(s):
                missing_videos.append(s)
                
        if not missing_videos:
            visual_score = 30
        else:
            deduction = len(missing_videos) * 7.5
            visual_score = max(0, 30 - deduction)
            feedback.append(f"Missing specific B-roll for: {', '.join(missing_videos)}")
            
        score += visual_score
            
        # ==========================================
        # 3. Audio (Max 20 points)
        # ==========================================
        audio_score = 0
        if duration > 0:
            audio_score += 10
        else:
            feedback.append("Voice track missing or zero duration.")
            
        if has_music:
            audio_score += 10
        else:
            feedback.append("Background music missing.")
            
        score += audio_score
            
        # ==========================================
        # 4. Technical (Max 10 points)
        # ==========================================
        tech_score = 0
        if 25 <= duration <= 90:
            tech_score += 10
        else:
            feedback.append(f"Duration {duration:.1f}s is outside ideal range (25s-90s).")
            
        score += tech_score
            
        passed = score >= self.min_passing_score
        
        logger.info(f"Reel Quality Score: {score}/100 (Content: {content_score}, Visual: {visual_score}, Audio: {audio_score}, Tech: {tech_score}). Passed: {passed}")
        for f in feedback:
            logger.info(f"Quality feedback: {f}")
            
        return {
            "score": score,
            "passed": passed,
            "feedback": feedback
        }

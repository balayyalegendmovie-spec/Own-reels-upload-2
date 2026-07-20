from typing import Dict, Any
from core.config import DEFAULT_VOICE

class VoiceDirector:
    """
    Analyzes the story and generates voice performance settings.
    """
    def __init__(self):
        pass

    def get_voice_config(self, story_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Determine voice configuration based on story emotion for each section.
        """
        # Base config parameters
        base_config = {
            "voice": DEFAULT_VOICE,
            "style": "young Telugu female creator",
            "age_feeling": 22,
            "accent": "neutral Telugu",
            "audience": "talking to one person",
            "smile": "slight",
            "breathing": "natural",
            "volume": "+40%"
        }

        configs = {}

        # Hook: High energy, rate +5%, pitch +10Hz, pause_length: 300
        configs["hook"] = base_config.copy()
        configs["hook"].update({
            "energy": 8,
            "rate": "+5%",
            "pitch": "+10Hz",
            "pause_length": 300
        })

        # Story: rate 0%, pitch 0Hz, pause_length: 500
        configs["story"] = base_config.copy()
        configs["story"].update({
            "energy": 5,
            "rate": "+0%",
            "pitch": "+0Hz",
            "pause_length": 500
        })

        # Emotional Payoff: rate -10%, pitch -5Hz, warmth features, pause_length: 600
        configs["emotional_payoff"] = base_config.copy()
        configs["emotional_payoff"].update({
            "energy": 3,
            "rate": "-10%",
            "pitch": "-5Hz",
            "smile": "warm",
            "pause_length": 600
        })

        # Lesson: rate -10%, pitch -5Hz, warmth features, pause_length: 600
        configs["lesson"] = base_config.copy()
        configs["lesson"].update({
            "energy": 3,
            "rate": "-10%",
            "pitch": "-5Hz",
            "smile": "warm",
            "pause_length": 600
        })

        # CTA: rate +10%, pitch +5Hz, pause_length: 0
        configs["cta"] = base_config.copy()
        configs["cta"].update({
            "energy": 7,
            "rate": "+10%",
            "pitch": "+5Hz",
            "pause_length": 0
        })

        return configs

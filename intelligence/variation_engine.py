import random
from typing import Dict, Any

class VariationEngine:
    """
    Prevents repetition by defining variations in video cropping,
    text positioning, animations, and opacity.
    """
    def __init__(self):
        pass

    def get_variation_config(self) -> Dict[str, Any]:
        """Generate random variation parameters."""
        styles = ["center", "bottom", "top"]
        animations = ["fade", "slide", "typewriter"]
        
        return {
            "text_style": random.choice(styles),
            "text_animation": random.choice(animations),
            "font_size": random.randint(60, 90),
            "opacity": round(random.uniform(0.7, 1.0), 2),
            "video_start_time": random.randint(0, 10), # Start video somewhere between 0 to 10 seconds
            "crop_offset_x": random.randint(-100, 100) # Slightly shift crop horizontally
        }

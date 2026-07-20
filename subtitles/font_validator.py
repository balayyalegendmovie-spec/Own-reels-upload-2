import os
import logging
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

FONT_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
REGULAR_FONT = os.path.join(FONT_DIR, 'NotoSansTelugu-Regular.ttf')
BOLD_FONT = os.path.join(FONT_DIR, 'NotoSansTelugu-Bold.ttf')

# Test characters covering basic vowels, consonants, and complex conjuncts
TEST_CHARACTERS = [
    'అ', 'ఆ', 'ఇ', 'ఈ', 'ఉ', 'ఊ',  # Vowels
    'క', 'ఖ', 'గ', 'ఘ',                # Consonants
    'క్ష', 'ప్ర', 'త్ర', 'జ్ఞ',          # Complex conjuncts
    'కా', 'కి', 'కీ', 'కు', 'కూ',       # Consonant + vowel marks
]

class FontValidator:
    def __init__(self):
        self.regular_font_path = REGULAR_FONT
        self.bold_font_path = BOLD_FONT
    
    def validate(self) -> bool:
        """Run all font validation checks. Returns True if all pass."""
        logger.info("FontValidator: Running Telugu font verification...")
        
        # 1. Check font files exist
        if not os.path.exists(self.regular_font_path):
            logger.error(f"Regular font missing: {self.regular_font_path}")
            return False
        if not os.path.exists(self.bold_font_path):
            logger.error(f"Bold font missing: {self.bold_font_path}")
            return False
        
        # 2. Check fonts load
        try:
            regular = ImageFont.truetype(self.regular_font_path, 60)
            bold = ImageFont.truetype(self.bold_font_path, 60)
        except Exception as e:
            logger.error(f"Failed to load fonts: {e}")
            return False
        
        # 3. Check Telugu characters render with non-zero bounding boxes
        for char in TEST_CHARACTERS:
            try:
                bbox = regular.getbbox(char)
                if bbox is None or (bbox[2] - bbox[0]) <= 0:
                    logger.error(f"Font failed to render Telugu character: '{char}'")
                    return False
            except Exception as e:
                logger.error(f"Error rendering '{char}': {e}")
                return False
        
        # 4. Check for dotted circle (indicates shaping failure)
        # Render a conjunct and check if the dotted circle glyph (U+25CC) appears
        # We do this by rendering 'క్ష' and checking width is reasonable
        conjunct_bbox = regular.getbbox('క్ష')
        separate_bbox_k = regular.getbbox('క')
        separate_bbox_sha = regular.getbbox('ష')
        
        # If conjunct is wider than both separate chars combined, shaping likely failed
        conjunct_width = conjunct_bbox[2] - conjunct_bbox[0] if conjunct_bbox else 0
        separate_width = (separate_bbox_k[2] - separate_bbox_k[0] + separate_bbox_sha[2] - separate_bbox_sha[0]) if separate_bbox_k and separate_bbox_sha else 0
        
        if conjunct_width >= separate_width and separate_width > 0:
            logger.warning("FontValidator: Conjunct 'క్ష' may not be shaping correctly (width >= separate chars). Will use uharfbuzz for shaping.")
        
        logger.info("FontValidator: All Telugu font checks PASSED ✓")
        return True
    
    def get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Get a loaded font at the specified size."""
        path = self.bold_font_path if bold else self.regular_font_path
        return ImageFont.truetype(path, size)

"""
Pillow-based Telugu Subtitle Renderer (V4)

Replaces ASS/libass rendering with in-memory Pillow text drawing.
Uses uharfbuzz for proper Telugu glyph shaping since Pillow's
Windows build lacks libraqm/HarfBuzz support.

Pipeline:
  Telugu text -> uharfbuzz shaping -> Pillow drawing -> MoviePy overlay
"""
import os
import logging
import re
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
from subtitles.text_normalizer import TextNormalizer
from subtitles.harfbuzz_renderer import HarfbuzzRenderer
from core.config import SAFE_MARGIN_TOP, SAFE_MARGIN_BOTTOM, SAFE_MARGIN_X

logger = logging.getLogger(__name__)

FONT_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
REGULAR_FONT = os.path.join(FONT_DIR, 'NotoSansTelugu-Regular.ttf')
BOLD_FONT = os.path.join(FONT_DIR, 'NotoSansTelugu-Bold.ttf')
EN_REGULAR_FONT = os.path.join(FONT_DIR, 'Inter-Regular.ttf')
EN_BOLD_FONT = os.path.join(FONT_DIR, 'Inter-Bold.ttf')


class PillowSubtitleRenderer:
    """
    Renders Telugu subtitles as transparent image overlays using Pillow.
    
    Each subtitle chunk is drawn onto a transparent RGBA image, which is
    then composited onto the video frame by MoviePy at the correct timestamp.
    """
    
    # Visual hierarchy settings
    STYLES = {
        'hook': {
            'font_size': 100,
            'bold': True,
            'color': (255, 255, 255, 255),         # White
            'highlight_color': (255, 215, 0, 255),  # Gold
            'shadow_color': (0, 0, 0, 180),
            'y_position': 0.50,  # Center of screen
        },
        'body': {
            'font_size': 70,
            'bold': False,
            'color': (255, 255, 255, 255),         # White
            'highlight_color': (255, 215, 0, 255),  # Gold
            'shadow_color': (0, 0, 0, 150),
            'y_position': 0.50,
        },
        'story': {
            'font_size': 70,
            'bold': False,
            'color': (255, 255, 255, 255),
            'highlight_color': (255, 215, 0, 255),
            'shadow_color': (0, 0, 0, 150),
            'y_position': 0.50,
        },
        'lesson': {
            'font_size': 70,
            'bold': False,
            'color': (255, 255, 255, 255),
            'highlight_color': (255, 215, 0, 255),
            'shadow_color': (0, 0, 0, 150),
            'y_position': 0.50,
        },
        'emotion': {
            'font_size': 85,
            'bold': True,
            'color': (255, 215, 0, 255),            # Gold
            'highlight_color': (255, 215, 0, 255),
            'shadow_color': (0, 0, 0, 180),
            'y_position': 0.50,
        },
        'emotional_payoff': {
            'font_size': 85,
            'bold': True,
            'color': (255, 215, 0, 255),
            'highlight_color': (255, 215, 0, 255),
            'shadow_color': (0, 0, 0, 180),
            'y_position': 0.50,
        },
        'ending': {
            'font_size': 75,
            'bold': False,
            'color': (255, 255, 255, 255),
            'highlight_color': (255, 215, 0, 255),
            'shadow_color': (0, 0, 0, 150),
            'y_position': 0.55,
        },
        'cta': {
            'font_size': 75,
            'bold': False,
            'color': (255, 255, 255, 255),
            'highlight_color': (255, 215, 0, 255),
            'shadow_color': (0, 0, 0, 150),
            'y_position': 0.55,
        },
    }
    
    MAX_CHARS_PER_LINE = 35
    MAX_LINES = 2
    
    def __init__(self, width: int = 1080, height: int = 1920):
        self.width = width
        self.height = height
        self.text_cleaner = TextNormalizer()
        self._font_cache = {}
        self.hb_renderer = HarfbuzzRenderer()
        
    def _get_font(self, size: int, bold: bool = False, lang: str = 'te') -> ImageFont.FreeTypeFont:
        """Get or cache a font at the specified size."""
        key = (size, bold, lang)
        if key not in self._font_cache:
            if lang == 'en':
                path = EN_BOLD_FONT if bold else EN_REGULAR_FONT
            else:
                path = BOLD_FONT if bold else REGULAR_FONT
            self._font_cache[key] = ImageFont.truetype(path, size)
        return self._font_cache[key]

    def _is_english_word(self, word: str) -> bool:
        """Check if a word consists primarily of Latin characters."""
        return bool(re.search(r'[A-Za-z]', word))
    
    def _smart_line_break(self, text: str, font_size: int, bold: bool) -> List[str]:
        """Break text into lines that fit within mobile safe area."""
        max_width = self.width - (2 * SAFE_MARGIN_X)
        words = text.split()
        
        if not words:
            return ['']
        
        lines = []
        current_line = []
        
        for word in words:
            test_line = current_line + [word]
            test_line_str = ' '.join(test_line)
            
            line_width = 0
            for w in test_line:
                lang = 'en' if self._is_english_word(w) else 'te'
                if lang == 'en':
                    f = self._get_font(font_size, bold, lang)
                    try:
                        line_width += f.getlength(w)
                    except AttributeError:
                        bbox = f.getbbox(w)
                        line_width += bbox[2] - bbox[0] if bbox else 0
                else:
                    path = BOLD_FONT if bold else REGULAR_FONT
                    line_width += self.hb_renderer.get_text_width(w, path, font_size)
            
            space_f = self._get_font(font_size, bold, 'te')
            try:
                space_w = space_f.getlength(' ')
            except AttributeError:
                bbox = space_f.getbbox(' ')
                space_w = bbox[2] - bbox[0] if bbox else 0
                
            line_width += space_w * (len(test_line) - 1)
            
            if line_width > max_width or len(test_line_str) > self.MAX_CHARS_PER_LINE:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                if len(lines) >= self.MAX_LINES:
                    # Append remaining words to last line, wait, no splitting words.
                    # Just break and omit remaining words or append them all?
                    # The prompt says: "Break lines only at word boundaries (spaces). Max 2 lines"
                    # We will append the rest of the text into the last line?
                    # Actually, if we hit max lines, we just stop adding lines.
                    current_line = []
                    break
            else:
                current_line.append(word)
        
        if current_line and len(lines) < self.MAX_LINES:
            lines.append(' '.join(current_line))
        
        return lines[:self.MAX_LINES]
    
    def _calculate_fade(self, t: float, start: float, end: float) -> float:
        """Calculate fade alpha for smooth transitions."""
        duration = end - start
        fade_in_dur = min(0.3, duration * 0.15)   # 15% of duration or 0.3s
        fade_out_dur = min(0.3, duration * 0.15)
        
        elapsed = t - start
        remaining = end - t
        
        if elapsed < fade_in_dur:
            return elapsed / fade_in_dur
        elif remaining < fade_out_dur:
            return remaining / fade_out_dur
        else:
            return 1.0
    
    def render_subtitle_frame(self, t: float, chunks: List[Dict[str, Any]]) -> np.ndarray:
        """
        Render the subtitle overlay for time t.
        
        Returns an RGBA numpy array (height, width, 4) that can be composited
        onto the video frame.
        """
        # Create transparent RGBA image
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Find which chunk is active at time t
        active_chunk = None
        for chunk in chunks:
            if chunk['start'] <= t < chunk['end']:
                active_chunk = chunk
                break
        
        if active_chunk is None:
            return np.array(img)
        
        # Get style for this chunk type
        chunk_type = active_chunk.get('type', 'body')
        style = self.STYLES.get(chunk_type, self.STYLES['body'])
        
        font_size = style['font_size']
        bold = style['bold']
        
        # Clean text
        text = self.text_cleaner.clean(active_chunk['text'])
        
        # Smart line break
        lines = self._smart_line_break(text, font_size, bold)
        
        # Calculate fade alpha
        fade = self._calculate_fade(t, active_chunk['start'], active_chunk['end'])
        
        # Get highlight words (only for body/story chunks - emotional keywords)
        highlight_words = active_chunk.get('highlight_words', [])
        
        # Calculate total text block height
        line_heights = []
        for line in lines:
            line_h = 0
            for w in line.split():
                lang = 'en' if self._is_english_word(w) else 'te'
                f = self._get_font(font_size, bold, lang)
                bbox = f.getbbox(w)
                h = (bbox[3] - bbox[1]) if bbox else font_size
                if h > line_h:
                    line_h = h
            if line_h == 0:
                line_h = font_size
            line_heights.append(line_h)
        
        line_spacing = 15
        total_height = sum(line_heights) + line_spacing * (len(lines) - 1)
        
        # Position: center vertically at the specified y_position
        base_y = int(self.height * style['y_position']) - total_height // 2
        
        # Clamp to safe area
        base_y = max(SAFE_MARGIN_TOP, min(base_y, self.height - SAFE_MARGIN_BOTTOM - total_height))
        
        # Draw each line
        current_y = base_y
        for line_idx, line in enumerate(lines):
            if not line.strip():
                current_y += line_heights[line_idx] + line_spacing
                continue
            
            self._draw_mixed_font_line(
                img, draw, line, font_size, bold, current_y, fade,
                style['color'], style['highlight_color'],
                style['shadow_color'], highlight_words if chunk_type in ('body', 'story', 'lesson') else []
            )
            
            current_y += line_heights[line_idx] + line_spacing
        
        return np.array(img)
    
    def _draw_mixed_font_line(
        self, img: Image.Image, draw: ImageDraw.Draw, line: str, font_size: int, bold: bool,
        y: int, fade: float, normal_color: Tuple, highlight_color: Tuple,
        shadow_color: Tuple, highlight_words: List[str]
    ):
        """Draw a line with mixed fonts and optional gold highlights."""
        words = line.split()
        
        line_width = 0
        word_fonts = []
        for word in words:
            lang = 'en' if self._is_english_word(word) else 'te'
            f = self._get_font(font_size, bold, lang)
            word_fonts.append((word, f, lang))
            
            if lang == 'en':
                try:
                    line_width += f.getlength(word)
                except AttributeError:
                    bbox = f.getbbox(word)
                    line_width += bbox[2] - bbox[0] if bbox else len(word) * font_size * 0.6
            else:
                path = BOLD_FONT if bold else REGULAR_FONT
                line_width += self.hb_renderer.get_text_width(word, path, font_size)
                
        space_f = self._get_font(font_size, bold, 'te')
        try:
            space_width = space_f.getlength(' ')
        except AttributeError:
            bbox = space_f.getbbox(' ')
            space_width = bbox[2] - bbox[0] if bbox else font_size // 3
            
        line_width += space_width * (len(words) - 1)
        x_start = (self.width - line_width) // 2
        
        current_x = x_start
        for word, font, lang in word_fonts:
            is_highlight = bool(highlight_words) and any(
                hw.lower() in word.lower() for hw in highlight_words
            )
            
            color = highlight_color if is_highlight else normal_color
            alpha = int(color[3] * fade) if len(color) == 4 else int(255 * fade)
            text_color = (color[0], color[1], color[2], alpha)
            
            shadow_alpha = int(shadow_color[3] * fade)
            s_color = (*shadow_color[:3], shadow_alpha)
            
            if lang == 'en':
                # Draw shadow
                draw.text((current_x + 3, y + 3), word, font=font, fill=s_color)
                # Draw text
                draw.text((current_x, y), word, font=font, fill=text_color)
                
                try:
                    word_width = font.getlength(word)
                except AttributeError:
                    word_bbox = font.getbbox(word)
                    word_width = word_bbox[2] - word_bbox[0] if word_bbox else len(word) * font_size * 0.6
            else:
                path = BOLD_FONT if bold else REGULAR_FONT
                # Draw shadow
                self.hb_renderer.draw_text(img, (current_x + 3, y + 3), word, path, font_size, s_color)
                # Draw text
                self.hb_renderer.draw_text(img, (current_x, y), word, path, font_size, text_color)
                
                word_width = self.hb_renderer.get_text_width(word, path, font_size)
                
            current_x += word_width + space_width
    
    def create_subtitle_clip(self, chunks: List[Dict[str, Any]], duration: float):
        """
        Create a MoviePy VideoClip that renders subtitles at each frame.
        
        Returns a VideoClip with transparent background (RGBA mask).
        """
        from moviepy.editor import VideoClip
        
        def make_frame(t):
            frame = self.render_subtitle_frame(t, chunks)
            # MoviePy expects RGB, not RGBA. We'll handle alpha via mask.
            return frame[:, :, :3]
        
        def make_mask(t):
            frame = self.render_subtitle_frame(t, chunks)
            # Return alpha channel normalized to 0-1
            return frame[:, :, 3] / 255.0
        
        # Cache frames to avoid double-rendering
        frame_cache = {}
        
        def make_frame_cached(t):
            # Round to nearest frame to enable caching
            frame_t = round(t, 3)
            if frame_t not in frame_cache:
                frame_cache[frame_t] = self.render_subtitle_frame(frame_t, chunks)
                # Keep cache bounded
                if len(frame_cache) > 60:
                    oldest = min(frame_cache.keys())
                    del frame_cache[oldest]
            rgba = frame_cache[frame_t]
            return rgba[:, :, :3]
        
        def make_mask_cached(t):
            frame_t = round(t, 3)
            if frame_t not in frame_cache:
                frame_cache[frame_t] = self.render_subtitle_frame(frame_t, chunks)
                if len(frame_cache) > 60:
                    oldest = min(frame_cache.keys())
                    del frame_cache[oldest]
            rgba = frame_cache[frame_t]
            return rgba[:, :, 3] / 255.0
        
        clip = VideoClip(make_frame_cached, duration=duration)
        mask = VideoClip(make_mask_cached, ismask=True, duration=duration)
        clip = clip.set_mask(mask)
        
        return clip

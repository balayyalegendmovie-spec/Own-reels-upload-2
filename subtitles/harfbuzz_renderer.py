import os
import uharfbuzz as hb
import freetype
import numpy as np
from PIL import Image
from typing import Tuple

class HarfbuzzRenderer:
    """
    Renders text using uharfbuzz for shaping and freetype-py for rasterization.
    This bypasses Pillow's lack of libraqm on Windows and ensures complex 
    scripts like Telugu (with gunintalu/conjuncts) are shaped correctly.
    """
    def __init__(self):
        self._hb_fonts = {}
        self._ft_faces = {}

    def _get_fonts(self, font_path: str, font_size: int):
        key = (font_path, font_size)
        if key not in self._hb_fonts:
            # Init HarfBuzz Font
            with open(font_path, 'rb') as f:
                font_data = f.read()
            face = hb.Face(font_data)
            hb_font = hb.Font(face)
            hb_font.scale = (font_size * 64, font_size * 64)
            hb.ot_font_set_funcs(hb_font)
            
            # Init Freetype Face
            ft_face = freetype.Face(font_path)
            ft_face.set_char_size(font_size * 64)
            
            self._hb_fonts[key] = hb_font
            self._ft_faces[key] = ft_face
            
        return self._hb_fonts[key], self._ft_faces[key]

    def get_text_width(self, text: str, font_path: str, font_size: int) -> int:
        hb_font, _ = self._get_fonts(font_path, font_size)
        
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(hb_font, buf)
        
        width = 0
        for pos in buf.glyph_positions:
            width += pos.x_advance / 64
        return int(width)

    def draw_text(self, image: Image.Image, position: Tuple[int, int], 
                  text: str, font_path: str, font_size: int, fill: Tuple):
        """Draws shaped text onto the given Pillow image."""
        if not text:
            return
            
        hb_font, ft_face = self._get_fonts(font_path, font_size)
        
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(hb_font, buf)
        
        infos = buf.glyph_infos
        positions = buf.glyph_positions
        
        start_x, start_y = position
        img_w, img_h = image.size
        
        alpha_layer = np.zeros((img_h, img_w), dtype=np.float32)
        
        pen_x = start_x
        pen_y = start_y + int(font_size * 0.8)  # Approximate baseline adjustment
        
        for info, pos in zip(infos, positions):
            ft_face.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER)
            bitmap = ft_face.glyph.bitmap
            
            if bitmap.width > 0 and bitmap.rows > 0:
                arr = np.array(bitmap.buffer, dtype=np.uint8).reshape((bitmap.rows, bitmap.width))
                
                draw_x = int(pen_x + (pos.x_offset / 64) + ft_face.glyph.bitmap_left)
                draw_y = int(pen_y - (pos.y_offset / 64) - ft_face.glyph.bitmap_top)
                
                y1, y2 = max(0, draw_y), min(img_h, draw_y + bitmap.rows)
                x1, x2 = max(0, draw_x), min(img_w, draw_x + bitmap.width)
                
                if y2 > y1 and x2 > x1:
                    arr_y1 = y1 - draw_y
                    arr_y2 = arr_y1 + (y2 - y1)
                    arr_x1 = x1 - draw_x
                    arr_x2 = arr_x1 + (x2 - x1)
                    
                    alpha_layer[y1:y2, x1:x2] = np.maximum(
                        alpha_layer[y1:y2, x1:x2], 
                        arr[arr_y1:arr_y2, arr_x1:arr_x2] / 255.0
                    )
            
            pen_x += pos.x_advance / 64
            pen_y -= pos.y_advance / 64
            
        r, g, b, a = fill if len(fill) == 4 else (*fill, 255)
        img_arr = np.array(image, dtype=np.float32)
        
        target_a = alpha_layer * (a / 255.0)
        dst_a = img_arr[:, :, 3] / 255.0
        out_a = target_a + dst_a * (1 - target_a)
        
        safe_out_a = np.where(out_a == 0, 1.0, out_a)
        
        for c, color_val in enumerate((r, g, b)):
            img_arr[:, :, c] = (color_val * target_a + img_arr[:, :, c] * dst_a * (1 - target_a)) / safe_out_a
            
        img_arr[:, :, 3] = out_a * 255.0
        image.paste(Image.fromarray(np.clip(img_arr, 0, 255).astype(np.uint8), 'RGBA'))

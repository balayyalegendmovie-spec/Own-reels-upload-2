import unicodedata
import re
import logging

logger = logging.getLogger(__name__)

class TeluguTextCleaner:
    """Cleans and normalizes Telugu text for reliable rendering."""
    
    # Dotted circle character that indicates shaping failure
    DOTTED_CIRCLE = '\u25CC'
    
    # Zero-width characters that can break rendering
    INVISIBLE_CHARS = [
        '\u200B',  # Zero Width Space
        '\u200C',  # Zero Width Non-Joiner  
        '\u200D',  # Zero Width Joiner
        '\uFEFF',  # BOM / Zero Width No-Break Space
        '\u00AD',  # Soft Hyphen
    ]
    
    def clean(self, text: str) -> str:
        """Full cleaning pipeline for Telugu text."""
        if not text:
            return text
            
        original = text
        
        # 1. Unicode NFC Normalization
        text = unicodedata.normalize('NFC', text)
        
        # 2. Remove dotted circles
        text = text.replace(self.DOTTED_CIRCLE, '')
        
        # 3. Remove problematic invisible characters
        # Keep ZWJ (\u200D) only if it's between two Telugu characters
        # (it's sometimes needed for proper conjunct formation)
        for char in self.INVISIBLE_CHARS:
            if char == '\u200D':  # ZWJ - handle specially
                # Remove ZWJ unless it's between two Telugu chars
                cleaned = []
                for i, c in enumerate(text):
                    if c == '\u200D':
                        # Keep only if between Telugu chars
                        prev_telugu = i > 0 and self._is_telugu(text[i-1])
                        next_telugu = i < len(text) - 1 and self._is_telugu(text[i+1])
                        if prev_telugu and next_telugu:
                            cleaned.append(c)
                        # else: skip it
                    else:
                        cleaned.append(c)
                text = ''.join(cleaned)
            else:
                text = text.replace(char, '')
        
        # 4. Remove unsupported Unicode combining marks that aren't Telugu
        cleaned_chars = []
        for char in text:
            cat = unicodedata.category(char)
            if cat.startswith('M'):  # Combining mark
                # Keep only Telugu combining marks (U+0C00-U+0C7F)
                if '\u0C00' <= char <= '\u0C7F':
                    cleaned_chars.append(char)
                # Also keep Latin combining marks for English words
                elif '\u0300' <= char <= '\u036F':
                    cleaned_chars.append(char)
                # else: drop it
            else:
                cleaned_chars.append(char)
        text = ''.join(cleaned_chars)
        
        # 5. Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        if text != original:
            logger.info(f"TeluguTextCleaner: Cleaned text (removed {len(original) - len(text)} chars)")
        
        return text
    
    def _is_telugu(self, char: str) -> bool:
        """Check if a character is in the Telugu Unicode block."""
        return '\u0C00' <= char <= '\u0C7F'
    
    def has_dotted_circles(self, text: str) -> bool:
        """Check if text contains dotted circle characters."""
        return self.DOTTED_CIRCLE in text

"""
Subtitle Engine V4

Parses word-level VTT timing from edge-tts and chunks it into
subtitle segments with type tags (hook/body/emotion/cta).

No longer generates ASS files. Instead, outputs structured chunks
that are consumed by the PillowSubtitleRenderer.
"""
import os
import logging
import re
from typing import Dict, Any, List, Tuple
from story_engine.hook_engine import HookEngine
from subtitles.text_normalizer import TextNormalizer

logger = logging.getLogger(__name__)


class SubtitleEngine:
    def __init__(self):
        self.hook_engine = HookEngine()
        self.text_cleaner = TextNormalizer()
        
    def _parse_time(self, time_str: str) -> float:
        """Convert SRT time string HH:MM:SS,mmm to seconds."""
        time_str = time_str.replace('.', ',')
        h, m, s_ms = time_str.split(':')
        s, ms = s_ms.split(',')
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0

    def parse_vtt(self, vtt_path: str, script: str = "", duration: float = 30.0) -> List[Dict[str, Any]]:
        """
        Parse VTT file and return structured subtitle chunks.
        
        Each chunk has:
          - start: float (seconds)
          - end: float (seconds)
          - text: str (cleaned Telugu text)
          - type: str (hook/body/emotion/ending/cta)
          - highlight_words: list[str] (words to highlight in gold)
        """
        if not os.path.exists(vtt_path):
            logger.error(f"VTT file not found: {vtt_path}")
            return []
            
        logger.info(f"Parsing VTT subtitles from {vtt_path}")
        
        # Read VTT
        with open(vtt_path, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            
        words_data = []
        for i in range(len(lines)):
            if '-->' in lines[i]:
                times = lines[i].split('-->')
                start_str = times[0].strip()
                end_str = times[1].strip()
                
                if i + 1 < len(lines):
                    text = lines[i+1]
                    words_data.append({
                        'start': self._parse_time(start_str),
                        'end': self._parse_time(end_str),
                        'text': self.text_cleaner.clean(text)
                    })
                    
        # Fallback if VTT was empty
        if not words_data and script:
            logger.warning("VTT was empty. Falling back to manual text chunking.")
            words = script.split()
            time_per_word = duration / max(1, len(words))
            for idx, w in enumerate(words):
                words_data.append({
                    'start': idx * time_per_word,
                    'end': (idx + 1) * time_per_word,
                    'text': self.text_cleaner.clean(w)
                })
                    
        # Chunk words into phrases
        chunks = []
        current_chunk = []
        
        max_words = 6
        for w in words_data:
            current_chunk.append(w)
            if re.search(r'[.?!,;]', w['text']) or len(current_chunk) >= max_words:
                chunks.append(current_chunk)
                current_chunk = []
                
        if current_chunk:
            chunks.append(current_chunk)
            
        # Enforce max words per screen (smart line breaking at chunk level)
        MAX_WORDS_PER_SCREEN = 8
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > MAX_WORDS_PER_SCREEN:
                part1 = chunk[:len(chunk)//2]
                part2 = chunk[len(chunk)//2:]
                
                mid_time = part1[0]['start'] + (part2[-1]['end'] - part1[0]['start']) / 2.0
                part1[-1]['end'] = mid_time
                part2[0]['start'] = mid_time
                
                final_chunks.extend([part1, part2])
            else:
                final_chunks.append(chunk)

        # Process through Hook Engine for type tagging
        processed_chunks = self.hook_engine.process_chunks(final_chunks)
        
        # Add highlight words (only important emotional words, not every word)
        for chunk in processed_chunks:
            chunk['highlight_words'] = self._select_highlight_words(
                chunk['text'], chunk['type']
            )
            # Clean the text one more time
            chunk['text'] = self.text_cleaner.clean(chunk['text'])

        return processed_chunks
    
    def _select_highlight_words(self, text: str, chunk_type: str) -> List[str]:
        """
        Select only emotionally important words to highlight.
        
        Rules:
        - Hook: highlight 1-2 key emotional words
        - Body/Story: highlight only the single most important word
        - Emotion: no highlighting needed (entire text is gold)
        - CTA: highlight action words
        """
        if chunk_type in ('emotion', 'emotional_payoff'):
            return []  # Entire chunk is gold, no need for word highlights
            
        words = text.split()
        if not words:
            return []
        
        # Emotional keywords to detect
        emotional_telugu = [
            'నిజం', 'బాధ', 'కలలు', 'ప్రేమ', 'హృదయం', 'కన్నీళ్లు',
            'బ్రతుకు', 'జీవితం', 'నమ్మకం', 'ధైర్యం', 'విజయం', 'శక్తి',
            'మార్పు', 'గెలుపు', 'ఓటమి', 'కష్టం', 'సంతోషం', 'బలం',
            'అద్భుతం', 'వదులుకోకు', 'నీలో', 'ప్రత్యేకం'
        ]
        emotional_english = [
            'life', 'career', 'feeling', 'mistake', 'secret',
            'follow', 'believe', 'power', 'success', 'dream',
            'change', 'ignore', 'important', 'special'
        ]
        
        highlights = []
        
        for word in words:
            clean_word = re.sub(r'[.?!,;]', '', word).strip()
            if not clean_word:
                continue
                
            # Check against emotional words
            is_emotional = any(
                ew in clean_word for ew in emotional_telugu
            ) or any(
                clean_word.lower() == ew for ew in emotional_english
            )
            
            if is_emotional:
                highlights.append(clean_word)
        
        # Limit highlights per chunk type
        if chunk_type == 'hook':
            return highlights[:2]  # Max 2 highlights in hook
        elif chunk_type in ('cta', 'ending'):
            return highlights[:1]  # Max 1 in CTA
        else:
            return highlights[:1]  # Max 1 in body/story/lesson

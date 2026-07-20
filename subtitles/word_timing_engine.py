import json
from typing import List, Dict

class WordTimingEngine:
    """
    Estimates word timings from sentence boundaries for languages/voices 
    that don't provide word-level timestamps (like edge-tts Telugu).
    """
    def __init__(self):
        pass

    def estimate_word_timings(self, sentence_events: List[Dict], output_path: str = None) -> List[Dict]:
        """
        Distribute the sentence duration across its words based on character weight.
        Output a list of dicts: {"word": "...", "start": 3.25, "end": 3.85}
        """
        words_timing = []
        
        for event in sentence_events:
            sentence_text = event.get('text', '')
            sentence_words = sentence_text.split()
            if not sentence_words:
                continue
                
            # offset and duration in 100-ns units
            start_ms = event['offset'] / 10000.0
            duration_ms = event['duration'] / 10000.0
            
            # calculate weight based on word length
            total_chars = sum(len(w) for w in sentence_words)
            if total_chars == 0:
                continue
                
            current_time = start_ms
            
            for w in sentence_words:
                w_chars = len(w)
                w_duration = duration_ms * (w_chars / total_chars)
                
                words_timing.append({
                    "word": w,
                    "start": round(current_time / 1000.0, 3),  # convert to seconds
                    "end": round((current_time + w_duration) / 1000.0, 3)
                })
                current_time += w_duration
                
        if output_path:
            # Output JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(words_timing, f, ensure_ascii=False, indent=2)
                
            # Also output VTT so subtitle engine can parse it
            vtt_path = output_path.replace('.json', '.vtt')
            with open(vtt_path, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                for w in words_timing:
                    start_str = self._format_vtt_time(w['start'])
                    end_str = self._format_vtt_time(w['end'])
                    f.write(f"{start_str} --> {end_str}\n{w['word']}\n\n")
                
        return words_timing

    def _format_vtt_time(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int(round((seconds % 1) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

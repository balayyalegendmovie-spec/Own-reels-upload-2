"""
TTS Engine V5

Generates Telugu voice using edge-tts with segmented generation for natural speech rhythm.
"""
import edge_tts
import asyncio
import logging
import os
from typing import Dict, Any, List, Tuple
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class TTSEngine:
    def __init__(self):
        pass

    async def _generate_segment(self, text: str, config: Dict[str, Any], output_path: str) -> List[Dict]:
        voice = config.get("voice", "te-IN-ShrutiNeural")
        rate = config.get("rate", config.get("speed", "+0%"))
        pitch = config.get("pitch", "+0Hz")
        volume = config.get("volume", "+40%")
        
        communicate = edge_tts.Communicate(
            text, 
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume
        )
        
        events = []
        with open(output_path, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
                elif chunk["type"] == "SentenceBoundary":
                    events.append(chunk)
                    
        return events

    async def generate_segmented_voice_async(self, story_data: Dict[str, Any], configs: Dict[str, Dict[str, Any]], 
                                     output_path: str) -> Tuple[str, List[Dict], Dict[str, Tuple[float, float]]]:
        parts = ["hook", "story", "emotional_payoff", "lesson", "cta"]
        
        final_audio = AudioSegment.empty()
        all_events = []
        section_timings = {}
        
        temp_dir = os.path.dirname(output_path)
        current_offset_ms = 0
        
        for part in parts:
            text = story_data.get(part, "")
            if not text:
                continue
                
            part_config = configs.get(part, {})
            part_path = os.path.join(temp_dir, f"temp_{part}.mp3")
            events = await self._generate_segment(text, part_config, part_path)
            
            part_audio = AudioSegment.from_mp3(part_path)
            
            start_time_sec = current_offset_ms / 1000.0
            
            # Shift events
            # edge_tts uses offset in 100-nanosecond units. 1 ms = 10,000 units.
            offset_in_100ns = current_offset_ms * 10000
            for event in events:
                shifted_event = event.copy()
                shifted_event['offset'] += offset_in_100ns
                all_events.append(shifted_event)
                
            final_audio += part_audio
            current_offset_ms += len(part_audio)
            
            end_time_sec = current_offset_ms / 1000.0
            section_timings[part] = (start_time_sec, end_time_sec)
            
            gap_ms = part_config.get("pause_length", 0)
            if gap_ms > 0:
                final_audio += AudioSegment.silent(duration=gap_ms)
                current_offset_ms += gap_ms
                
            # Cleanup temp file
            try:
                os.remove(part_path)
            except Exception:
                pass
                
        final_audio.export(output_path, format="mp3")
        
        logger.info(f"Generated segmented TTS audio at {output_path}")
        return output_path, all_events, section_timings
        
    def generate_segmented_voice(self, story_data: Dict[str, Any], configs: Dict[str, Dict[str, Any]], output_path: str) -> Tuple[str, List[Dict], Dict[str, Tuple[float, float]]]:
        """Synchronous wrapper for generating segmented voice"""
        return asyncio.run(self.generate_segmented_voice_async(story_data, configs, output_path))

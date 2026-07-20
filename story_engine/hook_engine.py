import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class HookEngine:
    def __init__(self):
        pass

    def process_chunks(self, chunks: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Takes the raw sentence chunks and tags them with animation styles:
        - hook: first 3 seconds or first sentence (strong entrance)
        - ending: last sentence (slow fade)
        - body: everything else (subtle fade)
        """
        logger.info("HookEngine: Processing chunks for retention optimization.")
        processed = []
        
        for i, chunk in enumerate(chunks):
            # Each chunk is a list of word dicts. We flatten it to a single text block
            start_time = chunk[0]['start']
            end_time = chunk[-1]['end']
            text = " ".join([w['text'] for w in chunk])
            
            chunk_type = "body"
            if i == 0 or start_time < 3.0:
                chunk_type = "hook"
            elif i == len(chunks) - 1:
                chunk_type = "ending"
            elif i == len(chunks) - 2 and len(chunks) > 3:
                chunk_type = "emotion"
                
            processed.append({
                "start": start_time,
                "end": end_time,
                "text": text,
                "type": chunk_type
            })
            
        return processed

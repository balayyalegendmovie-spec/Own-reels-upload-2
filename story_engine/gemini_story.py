import json
import logging
import requests
import os
from typing import Dict, Any
from core.config import GEMINI_API_KEY, GEMINI_API_KEY_2

logger = logging.getLogger(__name__)

class StoryEngine:
    def __init__(self, history_manager=None):
        self.use_fallback = False
        self.history_manager = history_manager
        if not GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set. Using local fallback templates.")
            self.use_fallback = True
            
    def _get_fallback_story(self, theme: str) -> Dict[str, Any]:
        """Provide a fallback story if Gemini is unavailable."""
        story = {
            "title": f"Fallback: {theme}",
            "category": "motivation",
            "emotion": "motivation",
            "voice_style": "casual",
            "hook_category": "emotion",
            "hook": "Guys ఒక్క నిమిషం ఆగి ఇది వినండి... ఇది మీ కోసమే.",
            "story": "మన life లో కొన్ని situations వస్తాయి కదా, మన మీద మనకే నమ్మకం ఉండదు. అందరూ మనల్ని తక్కువ చేసి చూస్తూ ఉంటారు. అప్పుడు మనం మన కోపాన్ని బయటపెట్టకుండా, మన టాలెంట్ తోనే వాళ్ళకి సమాధానం చెప్పాలి. కష్టాలు ఎప్పుడూ శాశ్వతం కాదు, కానీ ఆ కష్టాలను ఎదుర్కొనే నీ ధైర్యం మాత్రం శాశ్వతం.",
            "emotional_payoff": "ఎవరి కోసమో కాకుండా నీ కోసం బ్రతుకు, అప్పుడే నువ్వు నిజమైన విజయం సాధిస్తావు.",
            "lesson": "నీ వాల్యూ ఏంటో తెలుసుకో, ఎవరి ముందూ తల దించకు.",
            "cta": "ఈ మాటలు నీకు నచ్చితే తప్పకుండా ఈ వీడియోని save చేసుకో. follow for more daily motivation.",
            "caption": "మీరు ఎప్పుడైనా ఇలా ఫీల్ అయ్యారా? నిజం చెప్పండి 👇\n\nమన మీద మనకే నమ్మకం లేనప్పుడు, ఈ మాటలు గుర్తుచేసుకోండి. 🔥\n\n#telugu #telugumotivation #telugureels #inspiration #nevergiveup #viral",
            "hashtags": "#telugu #telugumotivation #telugureels #inspiration #nevergiveup #viral",
            "highlight_words": ["నిమిషం", "life", "నమ్మకం", "టాలెంట్", "ధైర్యం", "విజయం", "వాల్యూ", "follow"],
            "emotion_map": {"0-3": "curious", "3-15": "story", "15-30": "emotional"},
            "broll_keywords": {
                "hook": "person thinking deep",
                "story": "struggle focus working",
                "emotional_payoff": "success mountain view",
                "cta": "smartphone follow button"
            },
            "visual_direction": {
                "hook": "Close up of someone looking thoughtful or stressed.",
                "story": "Show progression from working hard to overcoming obstacles.",
                "emotional_payoff": "A wide, uplifting shot showing success or peace.",
                "cta": "Text overlay pointing to the follow button on a phone screen."
            }
        }
        story["script"] = f"{story['hook']} {story['story']} {story['emotional_payoff']} {story['lesson']} {story['cta']}".strip()
        return story
        
    def generate_story(self, theme: str) -> Dict[str, Any]:
        """
        Generate a conversational Telugu story based on the theme.
        Returns a dictionary with title, category, emotion, and script.
        """
        recent_hooks = "None"
        if self.history_manager:
            recent_stories = self.history_manager.history.get("stories_used", [])[-5:]
            recent_hooks = ", ".join([s.get("hook", "") if isinstance(s, dict) else s for s in recent_stories])
        
        prompt = f"""
        You are an expert Telugu content creator. Write a short, emotionally engaging Instagram Reel script.
        
        Theme: {theme}
        Recently used hooks to AVOID: {recent_hooks}
        
        Guidelines:
        1. Writing style MUST be a young Telugu girl talking conversationally with a close friend.
        2. Use natural, conversational Telugu mixed with common English words (e.g., "మన life లో కొన్ని situations వస్తాయి కదా" instead of textbook formal Telugu).
        3. Structure MUST strictly be: Hook -> Curiosity Gap -> Story -> Emotional Payoff -> CTA.
        4. Do NOT use emojis. Keep it highly relatable.
        5. Provide output strictly in JSON format as follows:
        {{
            "title": "Short title in English",
            "category": "One of: motivation, emotional, student life, career, relationships, peaceful",
            "emotion": "One of: sad, peace, motivation",
            "voice_style": "e.g., warm, casual, passionate",
            "hook_category": "One of: curiosity, question, emotion, surprise",
            "hook": "Strong engaging first sentence (5-12 words)",
            "story": "The core narrative",
            "emotional_payoff": "The peak emotional realization",
            "lesson": "The takeaway",
            "cta": "The call to action (CRITICAL: MUST ALWAYS BE PRESENT)",
            "caption": "A highly engaging Instagram caption summarizing the reel in Telugu & English. Include a hook, some value, and a question to drive comments.",
            "hashtags": "#telugu #telugumotivation #viral #trending (include 15-20 highly relevant and viral hashtags)",
            "highlight_words": ["important", "emotional", "words", "to", "highlight"],
            "emotion_map": {{"0-5": "curious", "5-35": "story"}},
            "broll_keywords": {{"hook": "...", "story": "...", "emotional_payoff": "...", "cta": "..."}},
            "visual_direction": {{"hook": "...", "story": "...", "emotional_payoff": "...", "cta": "..."}}
        }}
        
        For "broll_keywords" and "visual_direction", provide appropriate visual ideas for each section of the reel.
        
        Example Hook Style:
        "Guys... ఒక నిజం చెప్తాను. మనలో చాలామంది జీవితాన్ని మార్చే ఒక విషయం ignore చేస్తారు."
        
        Generate the JSON now.
        """
        
        if self.use_fallback:
            return self._get_fallback_story(theme)
            
        try:
            keys = [GEMINI_API_KEY]
            if GEMINI_API_KEY_2:
                keys.append(GEMINI_API_KEY_2)
                
            for i, key in enumerate(keys):
                try:
                    logger.info(f"Generating story for theme: {theme} (Using key {i+1})")
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={key}"
                    headers = {'Content-Type': 'application/json'}
                    payload = {
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }],
                        "generationConfig": {
                            "temperature": 0.9,
                            "topP": 0.95
                        }
                    }
                    response = requests.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    
                    # Parse Gemini response
                    res_json = response.json()
                    text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    # Clean up markdown formatting if the model wraps the response in ```json ... ```
                    if text.startswith("```json"):
                        text = text[7:]
                    if text.endswith("```"):
                        text = text[:-3]
                        
                    data = json.loads(text.strip())
                    
                    # Combine parts into a single script for TTS processing
                    data["script"] = f"{data.get('hook', '')} {data.get('story', '')} {data.get('emotional_payoff', '')} {data.get('lesson', '')} {data.get('cta', '')}".strip()
                    
                    return data
                except requests.exceptions.HTTPError as he:
                    if he.response.status_code == 429 and key != keys[-1]:
                        logger.warning("API key hit rate limit. Trying secondary key...")
                        continue
                    raise he
                    
        except Exception as e:
            logger.error(f"Error generating story: {e}. Using fallback.")
            return self._get_fallback_story(theme)

    def generate_new_topics(self, count: int = 5) -> list:
        """
        Brainstorm new topics when the queue runs dry.
        """
        if self.use_fallback:
            return [{"id": f"q_fallback_{i}", "topic": "life lessons", "emotion": "peaceful", "target_audience": "general", "language": "telugu", "style": "cinematic", "status": "pending"} for i in range(count)]
            
        recent_topics = "None"
        if self.history_manager:
            recent_stories = self.history_manager.history.get("stories_used", [])[-20:]
            recent_topics = ", ".join([s.get("theme", "") if isinstance(s, dict) else s for s in recent_stories])
            
        prompt = f"""
        You are an expert Instagram Reel strategist for a Telugu motivational page.
        I need {count} BRAND NEW, viral topic ideas for short video reels.
        
        Recent topics we ALREADY did (DO NOT REPEAT THESE): {recent_topics}
        
        Output strictly as a JSON array of objects with this schema:
        [
            {{
                "id": "q_unique_id",
                "topic": "The core concept (e.g., 'never comparing yourself to others')",
                "emotion": "One of: motivation, emotional, peace",
                "target_audience": "students, professionals, young adults, etc.",
                "language": "telugu",
                "style": "cinematic",
                "status": "pending"
            }}
        ]
        
        Generate {count} distinct JSON objects now. Do not include markdown formatting or anything outside the JSON array.
        """
        
        try:
            logger.info("Brainstorming new topics via Gemini...")
            keys = [GEMINI_API_KEY]
            if GEMINI_API_KEY_2:
                keys.append(GEMINI_API_KEY_2)
                
            for i, key in enumerate(keys):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={key}"
                    headers = {'Content-Type': 'application/json'}
                    payload = {
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }]
                    }
                    response = requests.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    
                    res_json = response.json()
                    text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    if text.startswith("```json"):
                        text = text[7:]
                    if text.endswith("```"):
                        text = text[:-3]
                        
                    data = json.loads(text.strip())
                    return data
                except requests.exceptions.HTTPError as he:
                    if he.response.status_code == 429 and key != keys[-1]:
                        logger.warning("API key hit rate limit. Trying secondary key...")
                        continue
                    raise he
                    
        except Exception as e:
            logger.error(f"Error generating new topics: {e}")
            return []

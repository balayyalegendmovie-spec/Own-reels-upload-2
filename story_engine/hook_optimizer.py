import logging
import random
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class HookOptimizer:
    """Optimizes hook text for maximum first-3-second retention."""
    
    # Hook categories with example patterns
    HOOK_CATEGORIES = {
        'curiosity': {
            'patterns': [
                'ఈ విషయం ఎవ్వరూ చెప్పరు...',
                'ఒక secret చెప్తాను...',
                'ఇది తెలిస్తే shock అవుతారు...',
            ],
            'style': 'mystery',
            'max_words': 10,
        },
        'question': {
            'patterns': [
                'నీ career గురించి ఇది తెలుసా?',
                'ఎందుకు అందరూ fail అవుతారో తెలుసా?',
                'నీకు ఇది అనిపించిందా ఎప్పుడైనా?',
            ],
            'style': 'direct_question',
            'max_words': 12,
        },
        'emotion': {
            'patterns': [
                'ఒక్కసారి ఆలోచించు...',
                'నిజం చెప్తాను... ఇది నన్ను బాగా hurt చేసింది.',
                'Guys... ఈ feeling మీకూ వచ్చిందా?',
            ],
            'style': 'vulnerable',
            'max_words': 12,
        },
        'surprise': {
            'patterns': [
                'ఇది నమ్మలేరు కానీ...',
                'Guys ఒక నిజం... ఇది మీ life మార్చేస్తుంది.',
                'నేను ఇది expect చేయలేదు...',
            ],
            'style': 'shock',
            'max_words': 10,
        },
    }
    
    MIN_HOOK_WORDS = 5
    MAX_HOOK_WORDS = 12
    MAX_HOOK_DURATION = 3.0  # seconds
    
    def classify_hook(self, hook_text: str) -> str:
        """Classify a hook into one of the categories."""
        hook_lower = hook_text.lower()
        
        # Question detection
        if '?' in hook_text or 'తెలుసా' in hook_text or 'ఎందుకు' in hook_text:
            return 'question'
        
        # Surprise detection
        if any(w in hook_lower for w in ['నమ్మలేరు', 'shock', 'expect', 'మార్చేస్తుంది']):
            return 'surprise'
        
        # Emotion detection
        if any(w in hook_lower for w in ['feeling', 'hurt', 'ఆలోచించు', 'బాధ']):
            return 'emotion'
        
        # Default to curiosity
        return 'curiosity'
    
    def validate_hook(self, hook_text: str) -> Dict[str, Any]:
        """Validate hook meets retention requirements."""
        words = hook_text.split()
        word_count = len(words)
        category = self.classify_hook(hook_text)
        
        result = {
            'valid': True,
            'category': category,
            'word_count': word_count,
            'issues': [],
        }
        
        if word_count < self.MIN_HOOK_WORDS:
            result['valid'] = False
            result['issues'].append(f'Hook too short: {word_count} words (min {self.MIN_HOOK_WORDS})')
        
        if word_count > self.MAX_HOOK_WORDS:
            result['valid'] = False
            result['issues'].append(f'Hook too long: {word_count} words (max {self.MAX_HOOK_WORDS})')
        
        if result['issues']:
            logger.warning(f"HookOptimizer: Hook validation issues: {result['issues']}")
        else:
            logger.info(f"HookOptimizer: Hook validated OK ({category}, {word_count} words)")
        
        return result
    
    def get_hook_style(self, category: str) -> Dict[str, Any]:
        """Get visual style settings for a hook category."""
        cat_data = self.HOOK_CATEGORIES.get(category, self.HOOK_CATEGORIES['curiosity'])
        return {
            'font_size': 100,
            'bold': True,
            'color': (255, 215, 0),  # Gold
            'animation': 'strong_entrance',
            'max_words': cat_data['max_words'],
            'style': cat_data['style'],
        }

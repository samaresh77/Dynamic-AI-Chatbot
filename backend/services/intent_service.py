import logging
from typing import Dict, Any
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

logger = logging.getLogger(__name__)

class IntentService:
    def __init__(self):
        try:
            self.intent_classifier = pipeline(
                "text-classification",
                model="joeddav/xlm-roberta-large-xnli",
                tokenizer="joeddav/xlm-roberta-large-xnli"
            )
        except Exception as e:
            logger.warning(f"Could not load intent classifier: {str(e)}")
            self.intent_classifier = None
        
        # Define common intents and patterns
        self.intent_patterns = {
            "greeting": ["hello", "hi", "hey", "good morning", "good afternoon"],
            "farewell": ["bye", "goodbye", "see you", "later"],
            "thanks": ["thank you", "thanks", "appreciate"],
            "weather": ["weather", "forecast", "temperature", "rain"],
            "time": ["time", "current time", "what time"],
            "help": ["help", "support", "assistance", "can you help"]
        }

    async def detect_intent(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        
        # Rule-based matching first
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return {
                    "intent": intent,
                    "confidence": 0.85,
                    "method": "rule_based"
                }
        
        # ML-based classification if available
        if self.intent_classifier:
            try:
                result = self.intent_classifier(text)
                return {
                    "intent": result[0]['label'],
                    "confidence": result[0]['score'],
                    "method": "ml_based"
                }
            except Exception as e:
                logger.error(f"Intent classification failed: {str(e)}")
        
        # Fallback
        return {
            "intent": "general",
            "confidence": 0.5,
            "method": "fallback"
        }
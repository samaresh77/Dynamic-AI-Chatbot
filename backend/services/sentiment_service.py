import logging
from typing import Dict, Any
from transformers import pipeline
import redis.asyncio as redis
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class SentimentService:
    def __init__(self):
        try:
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )
        except Exception as e:
            logger.warning(f"Could not load sentiment analyzer: {str(e)}")
            self.sentiment_analyzer = None
        
        # Simple rule-based sentiment as fallback
        self.sentiment_words = {
            "positive": ["good", "great", "excellent", "amazing", "wonderful", "happy"],
            "negative": ["bad", "terrible", "awful", "horrible", "sad", "angry"]
        }

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        # ML-based sentiment analysis
        if self.sentiment_analyzer:
            try:
                result = self.sentiment_analyzer(text)[0]
                return {
                    "label": result['label'],
                    "score": result['score'],
                    "method": "ml_based"
                }
            except Exception as e:
                logger.error(f"Sentiment analysis failed: {str(e)}")
        
        # Rule-based fallback
        return await self._rule_based_sentiment(text)

    async def _rule_based_sentiment(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        positive_count = sum(1 for word in self.sentiment_words["positive"] if word in text_lower)
        negative_count = sum(1 for word in self.sentiment_words["negative"] if word in text_lower)
        
        if positive_count > negative_count:
            return {"label": "POSITIVE", "score": 0.7, "method": "rule_based"}
        elif negative_count > positive_count:
            return {"label": "NEGATIVE", "score": 0.7, "method": "rule_based"}
        else:
            return {"label": "NEUTRAL", "score": 0.5, "method": "rule_based"}

    async def get_sentiment_trends(self) -> Dict[str, Any]:
        # This would typically analyze historical sentiment data
        # For now, return mock data
        return {
            "overall_sentiment": "positive",
            "positive_percentage": 65.2,
            "negative_percentage": 15.8,
            "neutral_percentage": 19.0,
            "trend": "improving"
        }
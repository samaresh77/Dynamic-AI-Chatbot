import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
import asyncio

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.metrics = {
            "total_conversations": 0,
            "average_response_time": 0.0,
            "user_satisfaction": 0.0,
            "common_intents": {},
            "error_rate": 0.0
        }
        
    async def track_interaction(self, session_id: str, user_message: str, response: Dict):
        # Update metrics
        self.metrics["total_conversations"] += 1
        
        response_time = response.get("response_time", 0)
        current_avg = self.metrics["average_response_time"]
        total_conv = self.metrics["total_conversations"]
        
        # Update running average
        self.metrics["average_response_time"] = (
            (current_avg * (total_conv - 1) + response_time) / total_conv
        )
        
        # Track common intents
        intent = response.get("intent", {}).get("intent", "unknown")
        if intent in self.metrics["common_intents"]:
            self.metrics["common_intents"][intent] += 1
        else:
            self.metrics["common_intents"][intent] = 1
            
        logger.info(f"Tracked interaction - Session: {session_id}, "
                   f"Intent: {intent}, Response Time: {response_time:.2f}s")

    async def get_conversation_analytics(self) -> Dict[str, Any]:
        return {
            "metrics": self.metrics,
            "timestamp": datetime.utcnow().isoformat(),
            "top_intents": dict(sorted(
                self.metrics["common_intents"].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5])
        }
        
import logging
import json
import time
from typing import Dict, Any, List
import openai
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import spacy
import redis.asyncio as redis

from config.settings import settings
from models.database import Conversation, UserSession
from services.intent_service import IntentService
from services.entity_service import EntityService
from services.sentiment_service import SentimentService

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.intent_service = IntentService()
        self.entity_service = EntityService()
        self.sentiment_service = SentimentService()
        self.context_memory = {}
        
        # Load NLP models
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found, downloading...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
        # Initialize GPT (fallback to local models if no API key)
        self.use_gpt = bool(settings.OPENAI_API_KEY)
        if self.use_gpt:
            openai.api_key = settings.OPENAI_API_KEY
        
        # Local response generation model
        self.response_generator = pipeline(
            "text-generation",
            model="microsoft/DialoGPT-medium",
            tokenizer="microsoft/DialoGPT-medium"
        )

    async def process_message(self, message: str, session_id: str) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            # Step 1: Analyze message
            intent = await self.intent_service.detect_intent(message)
            entities = await self.entity_service.extract_entities(message)
            sentiment = await self.sentiment_service.analyze_sentiment(message)
            
            # Step 2: Get context
            context = await self._get_context(session_id)
            
            # Step 3: Generate response
            response = await self._generate_response(
                message, intent, entities, sentiment, context, session_id
            )
            
            # Step 4: Update context
            await self._update_context(session_id, message, response, intent, entities)
            
            # Step 5: Calculate response time
            response_time = time.time() - start_time
            
            # Step 6: Store conversation
            await self._store_conversation(
                session_id, message, response, intent, entities, 
                sentiment, response_time
            )
            
            return {
                "response": response,
                "intent": intent,
                "entities": entities,
                "sentiment": sentiment,
                "response_time": response_time,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return await self._get_fallback_response(message)

    async def _generate_response(self, message: str, intent: Dict, entities: Dict, 
                               sentiment: Dict, context: Dict, session_id: str) -> str:
        
        # Rule-based responses for common intents
        rule_based_response = await self._get_rule_based_response(intent, entities)
        if rule_based_response:
            return rule_based_response
        
        # Try GPT-based response
        if self.use_gpt:
            try:
                return await self._get_gpt_response(message, context, sentiment)
            except Exception as e:
                logger.warning(f"GPT response failed: {str(e)}")
        
        # Fallback to local model
        return await self._get_local_response(message, context)

    async def _get_rule_based_response(self, intent: Dict, entities: Dict) -> str:
        intent_name = intent.get('intent', '')
        confidence = intent.get('confidence', 0)
        
        if confidence < 0.6:
            return ""
            
        responses = {
            "greeting": "Hello! How can I assist you today?",
            "farewell": "Goodbye! Feel free to reach out if you have more questions.",
            "thanks": "You're welcome! Is there anything else I can help with?",
            "weather": "I can help with weather information. Please provide a location.",
            "time": f"The current time is {time.strftime('%H:%M')}.",
            "help": "I'm here to help! You can ask me about various topics or seek assistance with specific queries."
        }
        
        return responses.get(intent_name, "")

    async def _get_gpt_response(self, message: str, context: Dict, sentiment: Dict) -> str:
        prompt = self._build_gpt_prompt(message, context, sentiment)
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()

    async def _get_local_response(self, message: str, context: Dict) -> str:
        # Use DialoGPT for local response generation
        conversation_history = context.get('history', [])
        history_text = " ".join(conversation_history[-5:])  # Last 5 messages
        
        input_text = f"{history_text} {message}"
        
        response = self.response_generator(
            input_text,
            max_length=100,
            num_return_sequences=1,
            pad_token_id=self.response_generator.tokenizer.eos_token_id
        )
        
        return response[0]['generated_text'].replace(input_text, '').strip()

    def _build_gpt_prompt(self, message: str, context: Dict, sentiment: Dict) -> str:
        prompt = f"""
        User message: {message}
        Sentiment: {sentiment.get('label', 'neutral')}
        Context: {context.get('last_intent', 'none')}
        
        Please provide a helpful, engaging response considering the user's sentiment and context.
        """
        return prompt

    async def _get_context(self, session_id: str) -> Dict:
        return self.context_memory.get(session_id, {
            'history': [],
            'last_intent': '',
            'entities': {},
            'sentiment_trend': 'neutral'
        })

    async def _update_context(self, session_id: str, message: str, response: str, 
                            intent: Dict, entities: Dict):
        if session_id not in self.context_memory:
            self.context_memory[session_id] = {
                'history': [],
                'last_intent': '',
                'entities': {},
                'sentiment_trend': 'neutral'
            }
        
        context = self.context_memory[session_id]
        context['history'].append(f"User: {message}")
        context['history'].append(f"Bot: {response}")
        context['last_intent'] = intent.get('intent', '')
        context['entities'].update(entities)
        
        # Keep only last 10 exchanges
        if len(context['history']) > 20:
            context['history'] = context['history'][-20:]

    async def _store_conversation(self, session_id: str, user_message: str, 
                                bot_response: str, intent: Dict, entities: Dict,
                                sentiment: Dict, response_time: float):
        # This would typically save to a database
        # For now, we'll just log it
        logger.info(f"Conversation stored - Session: {session_id}, "
                   f"Intent: {intent.get('intent')}, Response Time: {response_time:.2f}s")

    async def _get_fallback_response(self, message: str) -> Dict[str, Any]:
        return {
            "response": "I apologize, but I'm having trouble processing your request. Please try again.",
            "intent": {"intent": "error", "confidence": 0.0},
            "entities": {},
            "sentiment": {"label": "neutral", "score": 0.0},
            "response_time": 0.0,
            "session_id": "error"
        }
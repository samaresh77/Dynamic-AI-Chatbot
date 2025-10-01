from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
import redis.asyncio as redis
from datetime import datetime

from config.settings import settings
from services.chat_service import ChatService
from services.analytics_service import AnalyticsService
from services.sentiment_service import SentimentService
from models.database import init_db
from utils.cache import get_redis_pool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    app.state.redis = await get_redis_pool()
    app.state.chat_service = ChatService()
    app.state.analytics_service = AnalyticsService()
    app.state.sentiment_service = SentimentService()
    logger.info("Application started successfully")
    yield
    # Shutdown
    await app.state.redis.close()
    logger.info("Application shutdown")

app = FastAPI(
    title="Dynamic AI Chatbot API",
    description="Advanced conversational AI system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Dynamic AI Chatbot API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/chat")
async def chat_endpoint(message: dict):
    try:
        user_message = message.get("message", "")
        session_id = message.get("session_id", "default")
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        chat_service = app.state.chat_service
        response = await chat_service.process_message(user_message, session_id)
        
        # Track analytics
        await app.state.analytics_service.track_interaction(
            session_id, user_message, response
        )
        
        return JSONResponse(content=response)
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    chat_service = app.state.chat_service
    
    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message", "")
            session_id = data.get("session_id", "default")
            
            if user_message:
                response = await chat_service.process_message(user_message, session_id)
                await websocket.send_json(response)
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()

@app.get("/api/analytics/conversations")
async def get_conversation_analytics():
    analytics_service = app.state.analytics_service
    analytics = await analytics_service.get_conversation_analytics()
    return JSONResponse(content=analytics)

@app.get("/api/analytics/sentiment")
async def get_sentiment_analytics():
    sentiment_service = app.state.sentiment_service
    analytics = await sentiment_service.get_sentiment_trends()
    return JSONResponse(content=analytics)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
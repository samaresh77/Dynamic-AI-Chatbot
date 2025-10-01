import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./chatbot.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Hugging Face
    HUGGINGFACE_API_KEY: Optional[str] = None
    
    # JWT
    JWT_SECRET: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    
    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Model paths
    SENTIMENT_MODEL_PATH: str = "models/sentiment/"
    NER_MODEL_PATH: str = "models/ner/"
    
    class Config:
        env_file = ".env"

settings = Settings()
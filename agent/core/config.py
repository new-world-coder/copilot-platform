"""
Configuration settings for the Copilot Platform Agent
"""

import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Server settings
    HOST: str = "localhost"
    PORT: int = 8000
    DEBUG: bool = False
    
    # LLM settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_MODEL: str = "gpt-4"
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./copilot.db"
    
    # RAG settings
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    VECTOR_STORE_PATH: str = "./data/vector_store"
    
    # Task settings
    MAX_CONCURRENT_TASKS: int = 5
    TASK_TIMEOUT: int = 300  # 5 minutes
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

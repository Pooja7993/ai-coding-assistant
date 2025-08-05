"""
Core configuration module for the AI Coding Assistant.
"""
from typing import Optional, Literal
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # AI Model Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    model_name: str = Field(default="gpt-3.5-turbo", env="MODEL_NAME")
    max_tokens: int = Field(default=2000, env="MAX_TOKENS")
    
    # Memory and Vector Database
    memory_type: Literal["faiss", "chroma"] = Field(default="faiss", env="MEMORY_TYPE")
    vector_dimension: int = Field(default=384, env="VECTOR_DIMENSION")
    max_memory_size: int = Field(default=1000, env="MAX_MEMORY_SIZE")
    
    # Task Queue Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./app.db", env="DATABASE_URL")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: Literal["json", "text"] = Field(default="json", env="LOG_FORMAT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
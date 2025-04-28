from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Configuración general
    APP_NAME: str = "Multi-Agent System"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # Configuración de OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 2000
    
    # Configuración de logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Configuración de métricas
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Configuración de Sentry
    SENTRY_DSN: Optional[str] = None
    
    # Configuración del orquestador
    ORCHESTRATOR_MAX_RETRIES: int = 3
    ORCHESTRATOR_TIMEOUT: int = 30
    ORCHESTRATOR_CONFIDENCE_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

def get_settings() -> Settings:
    return settings 
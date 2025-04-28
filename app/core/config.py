from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Configuración de la aplicación
    APP_NAME: str = "Sistema Multi-Agente MCP"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # Sentry
    SENTRY_DSN: Optional[str] = None
    
    # Configuración de logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Configuración de agentes
    MAX_TOKENS: int = 4000
    TEMPERATURE: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings() 
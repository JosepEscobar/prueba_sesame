import os
from typing import Dict, Any, List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    # Configuración básica de la aplicación
    APP_NAME: str = "MultiAgentSystem"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    
    # Configuración de la base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    
    # Configuración de seguridad
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 semana
    
    # Configuración de CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Configuración de OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.2"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1000"))
    
    # Configuración de logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "json"
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    
    # Servicios externos
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "demo_key")
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "demo_key")
    BING_SEARCH_API_KEY: str = os.getenv("BING_SEARCH_API_KEY", "demo_key")
    
    # Configuración Model Context Protocol (MCP)
    MCP_SERVER_URL: str = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")
    MCP_API_KEY: str = os.getenv("MCP_API_KEY", "demo_mcp_key")
    
    # Configuración Prometheus para métricas
    METRICS_ENABLED: bool = os.getenv("METRICS_ENABLED", "True").lower() == "true"
    
    # Compatibilidad con nombres antiguos de variables
    API_V1_STR: str = API_PREFIX
    PROJECT_NAME: str = APP_NAME
    ENABLE_METRICS: bool = METRICS_ENABLED
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "9090"))
    ORCHESTRATOR_MAX_RETRIES: int = int(os.getenv("ORCHESTRATOR_MAX_RETRIES", "3"))
    ORCHESTRATOR_TIMEOUT: int = int(os.getenv("ORCHESTRATOR_TIMEOUT", "30"))
    ORCHESTRATOR_CONFIDENCE_THRESHOLD: float = float(os.getenv("ORCHESTRATOR_CONFIDENCE_THRESHOLD", "0.7"))
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Permite campos adicionales en .env sin causar errores


@lru_cache()
def get_settings() -> Settings:
    """Retorna una instancia cacheada de las configuraciones de la aplicación."""
    return Settings() 
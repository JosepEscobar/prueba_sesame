from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación."""

    # Configuración básica de la aplicación
    APP_NAME: str = "Multi-Agent System"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    VERSION: str = "0.1.0"

    # Configuración de la base de datos
    DATABASE_URL: str = "sqlite:///./app.db"

    # Configuración de seguridad
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 días

    # Configuración de CORS
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Configuración de OpenAI
    OPENAI_API_KEY: str = "sk-your-key-here"
    OPENAI_MODEL: str = "gpt-4o"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 1000

    # Configuración de logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "simple"  # "simple", "json"
    SENTRY_DSN: str | None = None

    # Configuración de métricas
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 8001

    # Configuración del orquestador
    ORCHESTRATOR_MAX_RETRIES: int = 3
    ORCHESTRATOR_TIMEOUT: int = 30
    ORCHESTRATOR_CONFIDENCE_THRESHOLD: float = 0.7

    # Configuración de servicios externos
    ALPHA_VANTAGE_API_KEY: str = "your-alpha-vantage-key"
    NEWS_API_KEY: str = "your-news-api-key"
    BING_SEARCH_API_KEY: str = "your-bing-search-key"

    # Configuración del servidor MCP
    MCP_ENABLED: bool = True
    MCP_HOST: str = "localhost"
    MCP_PORT: int = 4000

    # Configuración del cliente MCP
    MCP_CLIENT_URL: str = "http://localhost:4000"
    MCP_CLIENT_TIMEOUT: int = 30

    # Compatibilidad con nombres antiguos de variables
    API_V1_STR: str = API_PREFIX
    PROJECT_NAME: str = APP_NAME
    METRICS_ENABLED: bool = ENABLE_METRICS
    ORCHESTRATOR_MAX_RETRIES: int = ORCHESTRATOR_MAX_RETRIES
    ORCHESTRATOR_TIMEOUT: int = ORCHESTRATOR_TIMEOUT
    ORCHESTRATOR_CONFIDENCE_THRESHOLD: float = ORCHESTRATOR_CONFIDENCE_THRESHOLD
    ANTHROPIC_API_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, env_file_encoding="utf-8")

    @field_validator("API_PREFIX")
    def validate_api_prefix(cls, v: str) -> str:
        if not v.startswith("/"):
            return f"/{v}"
        return v


@lru_cache
def get_settings() -> Settings:
    """Retorna una instancia cacheada de las configuraciones de la aplicación."""
    return Settings()

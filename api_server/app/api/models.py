"""
Modelos Pydantic para la API
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
import time

class ErrorResponse(BaseModel):
    """Modelo para respuestas de error estandarizadas."""
    detail: str = Field(
        ..., 
        description="Descripción detallada del error",
        example="Error al procesar la consulta: invalid input format"
    )
    
    code: Optional[str] = Field(
        None, 
        description="Código de error para identificación programática",
        example="INVALID_INPUT"
    )
    
    timestamp: float = Field(
        default_factory=time.time,
        description="Marca de tiempo (epoch) cuando ocurrió el error",
        example=1633036800.1234
    )

class DataSource(BaseModel):
    """Información sobre una fuente de datos utilizada en una consulta."""
    name: str = Field(
        ..., 
        description="Nombre de la fuente de datos",
        example="MarketDatabase"
    )
    
    source_type: str = Field(
        ..., 
        description="Tipo de fuente (API, database, web, etc.)",
        example="API"
    )
    
    reliability: float = Field(
        ..., 
        description="Puntuación de confiabilidad de la fuente (0.0-1.0)",
        ge=0.0,
        le=1.0,
        example=0.85
    )
    
    timestamp: float = Field(
        default_factory=time.time,
        description="Marca de tiempo cuando se consultó la fuente",
        example=1633036800.1234
    )

class QueryRequest(BaseModel):
    """Modelo para solicitudes de consulta al sistema multi-agente."""
    query: str = Field(
        ..., 
        min_length=3, 
        max_length=2000,
        description="Consulta o pregunta del usuario",
        example="Analiza las tendencias actuales del mercado de comercio electrónico en España"
    )
    
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Contexto adicional para enriquecer la consulta",
        example={
            "industry": "Retail",
            "timeframe": "2022-2023",
            "region": "Europa",
            "focus_areas": ["Mobile commerce", "Last-mile delivery"]
        }
    )
    
    agent_preference: Optional[str] = Field(
        None,
        description="Preferencia de agente específico para procesar la consulta",
        example="analysis_agent"
    )
    
    @validator('query')
    def query_must_be_valid(cls, v):
        """Validador para asegurar que la consulta tiene un formato adecuado."""
        if len(v.strip()) < 3:
            raise ValueError('La consulta debe contener al menos 3 caracteres significativos')
        return v

class QueryResponse(BaseModel):
    """Modelo para respuestas de consultas procesadas por el sistema."""
    result: Dict[str, Any] = Field(
        ...,
        description="Resultado del procesamiento de la consulta",
        example={
            "content": "El análisis de las tendencias del mercado de comercio electrónico en España durante 2022-2023 revela...",
            "key_insights": ["Crecimiento del 23% en mobile commerce", "Aumento de métodos de pago alternativos"],
            "recommendations": ["Optimizar experiencia móvil", "Implementar múltiples opciones de pago"]
        }
    )
    
    agent: str = Field(
        ...,
        description="Identificador del agente que procesó la consulta",
        example="analysis_agent"
    )
    
    processing_time: float = Field(
        ...,
        description="Tiempo de procesamiento en segundos",
        example=1.45
    )
    
    confidence: float = Field(
        ...,
        description="Nivel de confianza de la respuesta (0.0-1.0)",
        ge=0.0,
        le=1.0,
        example=0.87
    )
    
    data_sources: Optional[List[DataSource]] = Field(
        None,
        description="Lista de fuentes de datos utilizadas para responder",
        example=[
            {
                "name": "Informe Sector Retail 2023",
                "source_type": "database",
                "reliability": 0.95,
                "timestamp": 1633036800.1234
            },
            {
                "name": "API MarketTrends",
                "source_type": "API",
                "reliability": 0.85,
                "timestamp": 1633036820.5678
            }
        ]
    )

class DataLookupRequest(BaseModel):
    """Modelo para solicitudes de búsqueda de datos externos."""
    lookup_type: str = Field(
        ...,
        description="Tipo de búsqueda a realizar (market, news, industry, web, company)",
        example="market"
    )
    
    query: Dict[str, Any] = Field(
        ...,
        description="Parámetros específicos para la búsqueda",
        example={
            "term": "ecommerce trends spain 2023",
            "limit": 5,
            "filter": "last_year"
        }
    )
    
    @validator('lookup_type')
    def valid_lookup_type(cls, v):
        """Validador para asegurar que el tipo de búsqueda es válido."""
        valid_types = ["market", "news", "industry", "web", "company"]
        if v not in valid_types:
            raise ValueError(f"Tipo de búsqueda no válido. Debe ser uno de: {', '.join(valid_types)}")
        return v
    
    @validator('query')
    def required_query_params(cls, v):
        """Validador para asegurar que los parámetros necesarios están presentes."""
        if "term" not in v or not v["term"]:
            raise ValueError("El parámetro 'term' es obligatorio en 'query'")
        return v

class DataLookupResponse(BaseModel):
    """Modelo para respuestas de búsquedas de datos externos."""
    success: bool = Field(
        ...,
        description="Indica si la búsqueda fue exitosa",
        example=True
    )
    
    result: Dict[str, Any] = Field(
        ...,
        description="Resultados de la búsqueda",
        example={
            "items": [
                {
                    "title": "Informe del mercado de comercio electrónico español 2023",
                    "source": "Market Research Institute",
                    "date": "2023-05-15",
                    "summary": "El mercado español de comercio electrónico creció un 18% en 2023...",
                    "link": "https://example.com/report/123"
                },
                {
                    "title": "Tendencias emergentes en retail online en España",
                    "source": "Ecommerce News",
                    "date": "2023-06-20",
                    "summary": "Las principales tendencias incluyen personalización...",
                    "link": "https://example.com/news/456"
                }
            ],
            "total_results": 24,
            "query_time": 0.12
        }
    )
    
    query: Dict[str, Any] = Field(
        ...,
        description="Parámetros utilizados para la búsqueda",
        example={
            "term": "ecommerce trends spain 2023",
            "limit": 5
        }
    )
    
    lookup_type: str = Field(
        ...,
        description="Tipo de búsqueda realizada",
        example="market"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadatos adicionales de la búsqueda",
        example={
            "data_freshness": "1 día",
            "coverage": "Spain, Portugal",
            "sources_used": 3
        }
    ) 
"""
Modelos Pydantic para la API
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    """Modelo para respuestas de error."""
    detail: str = Field(..., description="Descripción del error")
    error_code: Optional[str] = Field(None, description="Código de error interno")

class DataSource(BaseModel):
    """Modelo para representar una fuente de datos."""
    type: str = Field(..., description="Tipo de fuente (web, news, report, etc.)")
    source: str = Field(..., description="Nombre o identificador de la fuente")
    url: Optional[str] = Field(None, description="URL de la fuente, si está disponible")

class QueryRequest(BaseModel):
    """
    Modelo para solicitudes de consulta al sistema multi-agente.
    """
    query: str = Field(
        ..., 
        min_length=3, 
        max_length=2000,
        description="Consulta o pregunta del usuario"
    )
    context: Optional[Dict[str, Any]] = Field(
        default={}, 
        description="Contexto adicional para la consulta (opcional)"
    )
    agent_preference: Optional[str] = Field(
        None, 
        description="Preferencia de agente específico (opcional)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "query": "¿Cuáles son las mejores estrategias de marketing digital para una startup de fintech?",
                "context": {
                    "industry": "fintech",
                    "target_market": "millennials",
                    "budget": "limitado",
                    "competitors": ["Revolut", "N26", "Wise"]
                },
                "agent_preference": "marketing_agent"
            }
        }

class QueryResponse(BaseModel):
    """
    Modelo para respuestas del sistema multi-agente.
    """
    status: str = Field(..., description="Estado de la respuesta (success o error)")
    result: Optional[Union[Dict[str, Any], str]] = Field(
        None, 
        description="Resultado de la consulta o mensaje de error"
    )
    request_id: str = Field(..., description="Identificador único de la solicitud")
    processing_time: float = Field(
        ..., 
        description="Tiempo de procesamiento en segundos"
    )
    selected_agent: Optional[str] = Field(
        None, 
        description="Agente que procesó la consulta"
    )
    confidence: Optional[float] = Field(
        None, 
        description="Nivel de confianza del resultado (0.0 a 1.0)"
    )
    data_sources: Optional[List[DataSource]] = Field(
        None, 
        description="Fuentes de datos utilizadas para la respuesta"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "result": {
                    "analysis": "Las mejores estrategias de marketing digital para una startup de fintech...",
                    "recommendations": [
                        "Utilizar marketing de contenidos enfocado en educación financiera",
                        "Implementar campañas de marketing en redes sociales dirigidas a millennials",
                        "Desarrollar un programa de referidos con incentivos",
                        "Optimizar la presencia móvil y la experiencia de usuario",
                        "Establecer alianzas con influencers del sector financiero"
                    ]
                },
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "processing_time": 1.25,
                "selected_agent": "marketing_agent",
                "confidence": 0.87,
                "data_sources": [
                    {"type": "report", "source": "FinTech Trends 2023", "url": "https://example.com/report"},
                    {"type": "news", "source": "TechCrunch", "url": "https://techcrunch.com/article/123"}
                ]
            }
        }

class DataLookupRequest(BaseModel):
    """Modelo para solicitudes de búsqueda de datos"""
    query: Dict[str, Any] = Field(..., description="Parámetros de búsqueda")
    lookup_type: str = Field(..., description="Tipo de búsqueda (market, news, industry, web, company)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": {"term": "fintech latinoamerica", "limit": 5},
                "lookup_type": "news"
            }
        }

class DataLookupResponse(BaseModel):
    """Modelo para respuestas de búsqueda de datos"""
    success: bool = Field(True, description="Indica si la búsqueda fue exitosa")
    result: Any = Field(..., description="Resultado de la búsqueda")
    lookup_type: str = Field(..., description="Tipo de búsqueda realizada")
    query: Dict[str, Any] = Field(..., description="Parámetros de búsqueda utilizados")
    error: Optional[str] = Field(None, description="Mensaje de error si ocurrió alguno")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "result": [
                    {"title": "Crecimiento del sector fintech en LATAM", "source": "Financial Times", "date": "2023-05-10"},
                    {"title": "Nuevas regulaciones para fintech en Brasil", "source": "Bloomberg", "date": "2023-04-22"}
                ],
                "lookup_type": "news",
                "query": {"term": "fintech latinoamerica", "limit": 5},
                "error": None
            }
        } 
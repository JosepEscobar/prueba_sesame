from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Modelo para la solicitud de consulta al sistema multi-agente."""
    
    query: str = Field(
        ..., 
        description="La consulta o pregunta del usuario", 
        min_length=3, 
        example="¿Cuál es la mejor estrategia de marketing para una startup de tecnología?"
    )
    
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Contexto adicional para la consulta, como información de empresa, industria, etc.",
        example={
            "company": "TechStartup Inc.",
            "industry": "Software as a Service",
            "target_audience": "Pequeñas y medianas empresas",
            "budget": "Limitado"
        }
    )
    
    agent_preference: Optional[str] = Field(
        None,
        description="Preferencia opcional de un agente específico para procesar la consulta",
        example="marketing_agent"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadatos adicionales para la solicitud",
        example={
            "client_id": "app-web",
            "session_id": "abc123"
        }
    )


class QueryResponse(BaseModel):
    """Modelo para la respuesta de la consulta procesada."""
    
    result: Any = Field(
        ...,
        description="Resultado de la consulta procesada por el agente"
    )
    
    agent_used: str = Field(
        ...,
        description="Nombre del agente que procesó la consulta",
        example="marketing_agent"
    )
    
    request_id: str = Field(
        ...,
        description="Identificador único de la solicitud para seguimiento",
        example="c4b3f8a0-8f9e-4b1a-9e1a-0e1f3a1e0f1a"
    )
    
    processing_time: float = Field(
        ...,
        description="Tiempo de procesamiento en segundos",
        example=0.856
    )
    
    success: bool = Field(
        ...,
        description="Indicador de éxito del procesamiento",
        example=True
    )
    
    sources: Optional[List[str]] = Field(
        None,
        description="Fuentes de datos utilizadas para generar la respuesta",
        example=["Base de conocimiento interna", "Análisis de mercado 2023", "Tendencias de industria"]
    )
    
    confidence: Optional[float] = Field(
        None,
        description="Nivel de confianza del agente en su respuesta (0-1)",
        example=0.92,
        ge=0,
        le=1
    )


class ErrorResponse(BaseModel):
    """Modelo para respuestas de error."""
    
    error: str = Field(
        ...,
        description="Mensaje de error",
        example="Error al procesar la consulta: problema de conexión con el LLM"
    )
    
    request_id: Optional[str] = Field(
        None,
        description="Identificador único de la solicitud para seguimiento",
        example="c4b3f8a0-8f9e-4b1a-9e1a-0e1f3a1e0f1a"
    )
    
    success: bool = Field(
        False,
        description="Indicador de éxito (siempre falso para errores)",
        example=False
    )
    
    error_code: Optional[str] = Field(
        None,
        description="Código de error opcional para clasificar el tipo de error",
        example="AGENT_NOT_FOUND"
    ) 
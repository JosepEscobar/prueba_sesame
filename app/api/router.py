from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List

from app.core.config import settings
from app.core.logging import logger
from app.api.models import ErrorResponse

# Crear el router principal
api_router = APIRouter(
    prefix=settings.API_V1_STR,
    responses={
        400: {"model": ErrorResponse, "description": "Solicitud incorrecta"},
        404: {"model": ErrorResponse, "description": "Recurso no encontrado"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    }
)

# Endpoints para información sobre los agentes
@api_router.get("/agents", response_model=List[Dict[str, Any]])
async def get_available_agents():
    """
    Devuelve la lista de agentes disponibles en el sistema.
    
    Incluye información sobre sus capacidades y áreas de especialización.
    """
    try:
        agents_info = [
            {
                "id": "analysis_agent",
                "name": "Agente de Análisis",
                "description": "Analiza información compleja y proporciona resúmenes detallados.",
                "capabilities": [
                    "análisis de datos", 
                    "extracción de insights", 
                    "procesamiento de documentos", 
                    "resumen de información",
                    "identificación de patrones",
                    "análisis FODA"
                ]
            },
            {
                "id": "action_agent",
                "name": "Agente de Acción",
                "description": "Ejecuta acciones concretas y tareas operativas.",
                "capabilities": [
                    "automatización de tareas", 
                    "ejecución de procesos", 
                    "seguimiento de procedimientos", 
                    "implementación de soluciones",
                    "gestión de flujos de trabajo",
                    "optimización de operaciones"
                ]
            },
            {
                "id": "summary_agent",
                "name": "Agente de Resumen",
                "description": "Genera resúmenes concisos y puntos clave de información extensa.",
                "capabilities": [
                    "condensación de contenido", 
                    "extracción de puntos clave", 
                    "síntesis de información", 
                    "jerarquización de datos",
                    "resumen ejecutivo",
                    "priorización de información"
                ]
            },
            {
                "id": "finance_agent",
                "name": "Agente de Finanzas",
                "description": "Especialista en análisis financiero y consultoría económica.",
                "capabilities": [
                    "análisis financiero",
                    "planificación de presupuestos",
                    "optimización fiscal",
                    "estrategias de inversión",
                    "gestión de riesgos financieros",
                    "valuación empresarial",
                    "análisis de rentabilidad",
                    "modelos financieros",
                    "planificación de flujo de caja"
                ]
            },
            {
                "id": "marketing_agent",
                "name": "Agente de Marketing",
                "description": "Especialista en estrategias de marketing y análisis de mercado.",
                "capabilities": [
                    "estrategia de marketing",
                    "posicionamiento de marca",
                    "marketing digital",
                    "segmentación de mercado",
                    "análisis competitivo",
                    "estrategia de contenidos",
                    "optimización de canales",
                    "análisis de audiencia",
                    "customer journey",
                    "planificación de campañas"
                ]
            }
        ]
        
        return agents_info
        
    except Exception as e:
        logger.error(f"Error al obtener información de agentes: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al recuperar información de agentes disponibles"
        )

@api_router.get("/agents/{agent_id}", response_model=Dict[str, Any])
async def get_agent_info(agent_id: str):
    """
    Devuelve información detallada sobre un agente específico.
    
    Args:
        agent_id: Identificador del agente
    """
    # Lista de agentes disponibles
    available_agents = {
        "analysis_agent": {
            "id": "analysis_agent",
            "name": "Agente de Análisis",
            "description": "Analiza información compleja y proporciona resúmenes detallados.",
            "capabilities": [
                "análisis de datos", 
                "extracción de insights", 
                "procesamiento de documentos", 
                "resumen de información",
                "identificación de patrones",
                "análisis FODA"
            ],
            "created_at": "2023-06-15T12:00:00Z",
            "status": "active",
            "avg_confidence": 0.87,
            "success_rate": 0.92,
            "avg_response_time": 2.3
        },
        "action_agent": {
            "id": "action_agent",
            "name": "Agente de Acción",
            "description": "Ejecuta acciones concretas y tareas operativas.",
            "capabilities": [
                "automatización de tareas", 
                "ejecución de procesos", 
                "seguimiento de procedimientos", 
                "implementación de soluciones",
                "gestión de flujos de trabajo",
                "optimización de operaciones"
            ],
            "created_at": "2023-06-15T12:00:00Z",
            "status": "active",
            "avg_confidence": 0.85,
            "success_rate": 0.90,
            "avg_response_time": 1.8
        },
        "summary_agent": {
            "id": "summary_agent",
            "name": "Agente de Resumen",
            "description": "Genera resúmenes concisos y puntos clave de información extensa.",
            "capabilities": [
                "condensación de contenido", 
                "extracción de puntos clave", 
                "síntesis de información", 
                "jerarquización de datos",
                "resumen ejecutivo",
                "priorización de información"
            ],
            "created_at": "2023-06-15T12:00:00Z",
            "status": "active",
            "avg_confidence": 0.89,
            "success_rate": 0.94,
            "avg_response_time": 1.5
        },
        "finance_agent": {
            "id": "finance_agent",
            "name": "Agente de Finanzas",
            "description": "Especialista en análisis financiero y consultoría económica.",
            "capabilities": [
                "análisis financiero",
                "planificación de presupuestos",
                "optimización fiscal",
                "estrategias de inversión",
                "gestión de riesgos financieros",
                "valuación empresarial",
                "análisis de rentabilidad",
                "modelos financieros",
                "planificación de flujo de caja"
            ],
            "created_at": "2023-06-15T12:00:00Z",
            "status": "active",
            "avg_confidence": 0.89,
            "success_rate": 0.91,
            "avg_response_time": 2.7
        },
        "marketing_agent": {
            "id": "marketing_agent",
            "name": "Agente de Marketing",
            "description": "Especialista en estrategias de marketing y análisis de mercado.",
            "capabilities": [
                "estrategia de marketing",
                "posicionamiento de marca",
                "marketing digital",
                "segmentación de mercado",
                "análisis competitivo",
                "estrategia de contenidos",
                "optimización de canales",
                "análisis de audiencia",
                "customer journey",
                "planificación de campañas"
            ],
            "created_at": "2023-06-15T12:00:00Z",
            "status": "active",
            "avg_confidence": 0.87,
            "success_rate": 0.90,
            "avg_response_time": 2.5
        }
    }
    
    # Verificar si el agente existe
    if agent_id not in available_agents:
        logger.warning(f"Agente solicitado no encontrado: {agent_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Agente '{agent_id}' no encontrado"
        )
    
    return available_agents[agent_id]

# Endpoint para estadísticas del sistema
@api_router.get("/stats", response_model=Dict[str, Any])
async def get_system_stats():
    """
    Devuelve estadísticas generales del sistema multi-agente.
    
    Incluye métricas de rendimiento, uso y disponibilidad.
    """
    try:
        # En una implementación real, estas estadísticas vendrían de un servicio de métricas
        stats = {
            "total_requests": 12458,
            "successful_requests": 12215,
            "failed_requests": 243,
            "success_rate": 0.98,
            "avg_response_time": 2.3,
            "active_agents": 5,
            "agent_distribution": {
                "analysis_agent": 0.25,
                "action_agent": 0.15,
                "summary_agent": 0.10,
                "finance_agent": 0.30,
                "marketing_agent": 0.20
            },
            "system_uptime": 99.95,
            "last_restart": "2023-10-15T08:30:45Z",
            "api_version": settings.API_V1_STR.replace("/", "")
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas del sistema: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al recuperar estadísticas del sistema"
        ) 
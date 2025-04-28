from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, List
import time
import uuid

from app.core.logging import logger
from app.core.orchestrator import Orchestrator
from app.core.config import get_settings, Settings

# Modelo de datos para las solicitudes y respuestas
from app.api.models import QueryRequest, QueryResponse

api_router = APIRouter()

# Instancia del orquestador para procesar las consultas
orchestrator = Orchestrator()

# Dependencia para obtener configuraciones
def get_config():
    return get_settings()

@api_router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, request_obj: Request, config: Settings = Depends(get_config)):
    """
    Procesa una consulta utilizando el sistema multi-agente.
    
    La consulta se enruta automáticamente al agente especializado más apropiado
    según su contenido y contexto.
    """
    # Extraer request_id del middleware o generar uno nuevo
    request_id = getattr(request_obj.state, "request_id", str(uuid.uuid4()))
    
    # Convertir solicitud a diccionario
    query_data = request.dict()
    
    logger.info(
        f"Procesando consulta de usuario: {query_data.get('query', '')[:50]}...",
        extra={
            "request_id": request_id,
            "query_length": len(query_data.get("query", ""))
        }
    )
    
    try:
        # Procesar la consulta a través del orquestador
        result = orchestrator.process_request(query_data, request_id)
        
        # Verificar si hay errores
        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Error al procesar la consulta")
            )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Error procesando consulta: {str(e)}",
            extra={
                "request_id": request_id,
                "error": str(e)
            }
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la consulta: {str(e)}"
        )

@api_router.get("/agents", response_model=List[Dict[str, Any]])
async def get_available_agents(config: Settings = Depends(get_config)):
    """
    Retorna la lista de agentes disponibles en el sistema y sus capacidades.
    
    Esta información puede ser utilizada por el cliente para mostrar las opciones
    disponibles al usuario.
    """
    try:
        # Obtener información de los agentes a través del orquestador
        agents_info = [
            {
                "id": "router_agent",
                "name": "Agente Router",
                "description": "Agente que analiza consultas y las dirige al especialista más adecuado.",
                "capabilities": [
                    "análisis de consultas",
                    "categorización de preguntas",
                    "enrutamiento de solicitudes",
                    "delegación de tareas"
                ]
            },
            {
                "id": "analysis_agent",
                "name": "Agente de Análisis",
                "description": "Especialista en análisis detallado de información y situaciones empresariales.",
                "capabilities": [
                    "análisis de datos",
                    "evaluación de situaciones",
                    "identificación de patrones",
                    "extracción de insights",
                    "análisis de tendencias"
                ]
            },
            {
                "id": "action_agent",
                "name": "Agente de Acción",
                "description": "Especialista en recomendaciones prácticas y planes de acción.",
                "capabilities": [
                    "planificación estratégica",
                    "recomendaciones tácticas",
                    "planes de implementación",
                    "priorización de acciones",
                    "definición de procesos"
                ]
            },
            {
                "id": "summary_agent",
                "name": "Agente de Resumen",
                "description": "Especialista en sintetizar información compleja en formato conciso.",
                "capabilities": [
                    "condensación de contenido",
                    "extracción de puntos clave",
                    "síntesis de información",
                    "estructuración de resúmenes",
                    "simplificación de conceptos"
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
def get_agent_info(agent_id: str):
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
def get_system_stats():
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
            "api_version": config.API_V1_STR.replace("/", "")
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas del sistema: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al recuperar estadísticas del sistema"
        )

@api_router.post("/lookup", response_model=Dict[str, Any])
def data_lookup(query: Dict[str, Any]):
    """
    Realiza una búsqueda de datos utilizando el servicio de integración de datos.
    
    Args:
        query: Diccionario con parámetros para la búsqueda
    """
    try:
        lookup_service = DataLookupService()
        lookup_type = query.get("type", "market")
        search_term = query.get("query", "")
        
        if not search_term:
            raise HTTPException(
                status_code=400,
                detail="El parámetro 'query' es obligatorio"
            )
        
        # Realizar la búsqueda según el tipo especificado
        if lookup_type == "market":
            result = lookup_service.search_market_data(search_term)
        elif lookup_type == "news":
            result = lookup_service.search_news(search_term)
        elif lookup_type == "industry":
            result = lookup_service.search_industry_reports(search_term)
        elif lookup_type == "web":
            result = lookup_service.search_web(search_term)
        elif lookup_type == "company":
            result = lookup_service.lookup_company_data(search_term)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de búsqueda no válido: {lookup_type}"
            )
        
        return {
            "success": True,
            "result": result,
            "query": search_term,
            "type": lookup_type
        }
        
    except Exception as e:
        logger.error(f"Error en la búsqueda de datos: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al realizar la búsqueda: {str(e)}"
        ) 
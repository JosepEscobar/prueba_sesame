from fastapi import APIRouter, HTTPException, Depends, Request, status, BackgroundTasks
from typing import Dict, Any, List
import time
import uuid

from app.core.logging import logger
from app.core.orchestrator import Orchestrator
from app.core.config import get_settings, Settings
from app.services.data_lookup import DataLookupService
from app.core.metrics import MetricsCollector

# Modelo de datos para las solicitudes y respuestas
from app.api.models import QueryRequest, QueryResponse, DataLookupRequest, DataLookupResponse, ErrorResponse

from app.api.endpoints import tools

# Crear router de la API
api_router = APIRouter()

# Instancia del orquestador para procesar las consultas
orchestrator = Orchestrator()

# Instancia del servicio de búsqueda de datos
data_lookup_service = DataLookupService()

# Dependencia para obtener configuraciones
def get_config():
    return get_settings()

# Incluir routers de endpoints
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])

@api_router.post(
    "/query", 
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Error de validación en la entrada"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    },
    summary="Procesar una consulta mediante el sistema multi-agente",
    description="""
    Envía una consulta al sistema multi-agente para su procesamiento. El sistema:
    1. Analizará la consulta para determinar el agente más adecuado
    2. Procesará la consulta utilizando el agente seleccionado
    3. Devolverá el resultado con metadatos sobre el procesamiento

    Se puede proporcionar contexto adicional para mejorar la precisión de la respuesta, 
    así como una preferencia de agente específico para el procesamiento.
    """
)
async def process_query(
    request: Dict[str, Any], 
    background_tasks: BackgroundTasks, 
    req: Request
):
    """
    Procesa una consulta utilizando el sistema multi-agente.
    
    La consulta es enrutada al agente más adecuado para procesarla.
    
    Args:
        request: Diccionario con la consulta y contexto opcional
        background_tasks: Tareas en segundo plano para métricas
        req: Objeto Request de FastAPI
        
    Returns:
        Respuesta del sistema multi-agente
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Procesando consulta (request_id: {request_id})")
    
    start_time = time.time()
    
    try:
        result = await orchestrator.process_query(request)
        
        # Calcular tiempo de procesamiento
        processing_time = time.time() - start_time
        
        # Registrar métricas en segundo plano
        background_tasks.add_task(
            MetricsCollector.record_query_execution,
            success=True,
            agent=result.get("agent", "unknown"),
            confidence=result.get("confidence", 0.0),
            execution_time=processing_time
        )
        
        logger.info(f"Consulta procesada en {processing_time:.4f}s por {result.get('agent', 'unknown')} (request_id: {request_id})")
        
        # Agregar metadatos a la respuesta
        result["metadata"] = {
            "request_id": request_id,
            "processing_time": processing_time,
            "agent": result.get("agent", "unknown"),
            "confidence": result.get("confidence", 0.0)
        }
        
        return result
        
    except Exception as e:
        # Calcular tiempo en caso de error
        processing_time = time.time() - start_time
        
        # Registrar métricas en segundo plano
        background_tasks.add_task(
            MetricsCollector.record_query_execution,
            success=False,
            agent="error",
            confidence=0.0,
            execution_time=processing_time,
            error=str(e)
        )
        
        logger.error(f"Error al procesar consulta: {str(e)} (request_id: {request_id})")
        
        return {
            "result": {
                "error": "Error al procesar la consulta",
                "detail": str(e)
            },
            "agent": "error",
            "processing_time": processing_time,
            "confidence": 0.0,
            "metadata": {
                "request_id": request_id,
                "success": False
            }
        }

@api_router.get(
    "/agents", 
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Obtener lista de agentes disponibles",
    description="""
    Devuelve información sobre todos los agentes disponibles en el sistema multi-agente.
    
    Para cada agente, se incluye:
    - Identificador único
    - Nombre descriptivo
    - Tipo de agente
    - Descripción de capacidades
    - Métricas de rendimiento (tasa de éxito, tiempo promedio de respuesta)
    
    Esta información es útil para entender las capacidades del sistema y para decidir
    qué agente especificar en las solicitudes de consulta si se desea uno en particular.
    """
)
async def get_available_agents():
    try:
        agents = orchestrator.get_available_agents()
        return agents
    except Exception as e:
        logger.error(f"Error fetching available agents: {str(e)}")
        MetricsCollector.record_error("orchestrator", "fetch_agents")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener agentes disponibles: {str(e)}"
        )

@api_router.get(
    "/agents/{agent_id}", 
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Agente no encontrado"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    },
    summary="Obtener información detallada de un agente específico",
    description="""
    Devuelve información detallada sobre un agente específico identificado por su ID.
    
    La respuesta incluye:
    - Información básica (nombre, tipo, descripción)
    - Capacidades detalladas del agente
    - Métricas de rendimiento (tasa de éxito, tiempo promedio, precisión)
    - Estadísticas de uso (número de consultas procesadas, tendencias)
    - Configuración técnica (modelo utilizado, parámetros)
    
    Esta información es útil para comprender en profundidad las capacidades
    y el rendimiento de un agente específico antes de utilizarlo.
    """
)
async def get_agent_info(agent_id: str):
    try:
        agent_info = orchestrator.get_agent_info(agent_id)
        if not agent_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agente con ID '{agent_id}' no encontrado"
            )
        return agent_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agent info for {agent_id}: {str(e)}")
        MetricsCollector.record_error("orchestrator", "fetch_agent_info")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener información del agente: {str(e)}"
        )

@api_router.get(
    "/stats", 
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Obtener estadísticas del sistema multi-agente",
    description="""
    Devuelve estadísticas detalladas sobre el rendimiento y uso del sistema multi-agente.
    
    Las estadísticas incluyen:
    - Métricas de rendimiento global (tasa de éxito, tiempo promedio de respuesta)
    - Distribución de consultas por tipo de agente
    - Métricas de rendimiento por agente
    - Tendencias de uso a lo largo del tiempo
    - Estadísticas de errores y excepciones
    - Métricas de recursos (uso de CPU, memoria, tokens)
    
    Esta información es valiosa para monitorear la salud y rendimiento del sistema,
    identificar áreas de mejora, y entender patrones de uso.
    """
)
async def get_system_stats():
    try:
        stats = orchestrator.get_system_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching system stats: {str(e)}")
        MetricsCollector.record_error("orchestrator", "fetch_stats")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas del sistema: {str(e)}"
        )

@api_router.post(
    "/lookup", 
    response_model=DataLookupResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Error de validación en la solicitud"},
        500: {"model": ErrorResponse, "description": "Error durante la búsqueda de datos"}
    },
    summary="Buscar información en fuentes de datos externas",
    description="""
    Realiza búsquedas de información en diversas fuentes de datos externas.
    
    Tipos de búsqueda disponibles:
    - **market**: Datos de mercado y análisis económicos
    - **news**: Noticias recientes y artículos
    - **industry**: Informes y estadísticas de industrias específicas
    - **web**: Búsqueda general en internet
    - **company**: Información detallada sobre empresas específicas
    
    La solicitud debe especificar el tipo de búsqueda y los parámetros de consulta
    relevantes, como términos de búsqueda, filtros y límites.
    
    Los resultados incluirán la información obtenida, metadatos sobre la búsqueda
    y detalles sobre las fuentes utilizadas.
    """
)
async def lookup_data(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Busca información en fuentes externas.
    
    Args:
        request: Diccionario con el tipo de búsqueda y parámetros
        background_tasks: Tareas en segundo plano para métricas
        
    Returns:
        Resultados de la búsqueda
        
    Raises:
        HTTPException: Si el tipo de búsqueda no es válido
    """
    request_id = str(uuid.uuid4())
    lookup_type = request.get("type", "")
    query = request.get("query", "")
    
    logger.info(f"Realizando búsqueda de tipo '{lookup_type}': '{query}' (request_id: {request_id})")
    
    start_time = time.time()
    
    # Utilizar el servicio de búsqueda del orquestador
    data_lookup = orchestrator.data_lookup_service
    
    try:
        result = {}
        
        # Ejecutar el tipo de búsqueda adecuado
        if lookup_type == "market":
            result = data_lookup.search_market_data(query)
        elif lookup_type == "news":
            result = data_lookup.search_news(query)
        elif lookup_type == "industry":
            industry = request.get("industry", "")
            result = data_lookup.search_industry_reports(industry)
        elif lookup_type == "web":
            result = data_lookup.search_web(query)
        elif lookup_type == "company":
            company = request.get("company", "")
            result = data_lookup.lookup_company_data(company)
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de búsqueda no válido: {lookup_type}"
            )
        
        # Calcular tiempo de procesamiento
        processing_time = time.time() - start_time
        
        # Registrar métricas en segundo plano
        background_tasks.add_task(
            MetricsCollector.record_lookup_execution,
            lookup_type=lookup_type,
            success=True,
            execution_time=processing_time
        )
        
        logger.info(f"Búsqueda '{lookup_type}' completada en {processing_time:.4f}s (request_id: {request_id})")
        
        # Formatear la respuesta según el modelo DataLookupResponse
        response = {
            "success": True,
            "result": result,
            "query": {"term": query},
            "lookup_type": lookup_type,
            "metadata": {
                "request_id": request_id,
                "lookup_type": lookup_type,
                "processing_time": processing_time
            }
        }
        
        return response
        
    except Exception as e:
        # Calcular tiempo en caso de error
        processing_time = time.time() - start_time
        
        # Registrar métricas en segundo plano
        background_tasks.add_task(
            MetricsCollector.record_lookup_execution,
            lookup_type=lookup_type,
            success=False,
            execution_time=processing_time,
            error=str(e)
        )
        
        logger.error(f"Error en búsqueda '{lookup_type}': {str(e)} (request_id: {request_id})")
        
        return {
            "success": False,
            "result": {"error": f"Error al realizar búsqueda de tipo '{lookup_type}'", "detail": str(e)},
            "query": {"term": query},
            "lookup_type": lookup_type,
            "metadata": {
                "request_id": request_id,
                "processing_time": processing_time,
                "success": False
            }
        } 
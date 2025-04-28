"""
Rutas de la API para el sistema multi-agente
"""

import time
import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.core.logging import logger
from app.api.models import (
    QueryRequest, 
    QueryResponse, 
    DataLookupRequest, 
    DataLookupResponse, 
    ErrorResponse
)
from app.agents.router_agent import RouterAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.action_agent import ActionAgent
from app.agents.summary_agent import SummaryAgent
from app.services.data_lookup import DataLookupService

router = APIRouter()

# Instancias de los agentes
router_agent = RouterAgent(name="router_agent")
analysis_agent = AnalysisAgent(name="analysis_agent")
action_agent = ActionAgent(name="action_agent")
summary_agent = SummaryAgent(name="summary_agent")

# Servicio de búsqueda de datos
data_lookup_service = DataLookupService()

# Diccionario para mapear tipos de agentes a instancias
AGENTS = {
    "router": router_agent,
    "analysis": analysis_agent,
    "action": action_agent,
    "summary": summary_agent
}

@router.post("/query", response_model=QueryResponse, responses={500: {"model": ErrorResponse}})
async def process_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Procesa una consulta utilizando el sistema multi-agente.
    Si no se especifica un agent_type, se utiliza el router_agent para determinar
    cuál es el agente más adecuado para procesar la consulta.
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Procesando consulta: {request.query}", extra={"request_id": request_id})
        
        # Determinar qué agente usar
        if request.agent_type and request.agent_type in AGENTS:
            agent = AGENTS[request.agent_type]
            agent_name = request.agent_type
            logger.info(f"Usando agente específico: {agent_name}", extra={"request_id": request_id})
        else:
            # Usar el agente de enrutamiento para determinar el mejor agente
            logger.info("Determinando el mejor agente para la consulta", extra={"request_id": request_id})
            router_result = router_agent.execute({
                "query": request.query,
                "context": request.context or {}
            })
            
            agent_name = router_result["agent"].lower()
            if agent_name not in AGENTS:
                logger.warning(f"Agente no reconocido: {agent_name}, usando analysis_agent", 
                              extra={"request_id": request_id})
                agent_name = "analysis"
            
            agent = AGENTS[agent_name]
            logger.info(f"Agente seleccionado: {agent_name}", extra={"request_id": request_id})
        
        # Ejecutar el agente elegido
        result = agent.execute({
            "query": request.query,
            "context": request.context or {}
        })
        
        processing_time = time.time() - start_time
        
        # Registro de métricas en segundo plano
        background_tasks.add_task(
            logger.info,
            f"Consulta completada por {agent_name} en {processing_time:.2f}s",
            extra={
                "request_id": request_id,
                "processing_time": processing_time,
                "agent": agent_name
            }
        )
        
        return QueryResponse(
            request_id=request_id,
            result=result["result"],
            agent_used=agent_name,
            confidence=result.get("confidence", 0.0),
            processing_time=processing_time,
            success=True,
            sources=result.get("sources")
        )
        
    except Exception as e:
        logger.error(f"Error al procesar consulta: {str(e)}", 
                    extra={"request_id": request_id, "error": str(e)})
        processing_time = time.time() - start_time
        
        return QueryResponse(
            request_id=request_id,
            result="",
            agent_used="error",
            confidence=0.0,
            processing_time=processing_time,
            success=False,
            error=str(e)
        )

@router.post("/data-lookup", response_model=DataLookupResponse)
async def lookup_data(request: DataLookupRequest):
    """
    Busca información utilizando el servicio DataLookupService.
    Permite buscar datos de mercado, noticias, informes de industria, 
    información web o datos de empresas.
    """
    try:
        lookup_type = request.lookup_type.lower()
        query = request.query
        
        if lookup_type == "market":
            result = data_lookup_service.search_market_data(**query)
        elif lookup_type == "news":
            result = data_lookup_service.search_news(**query)
        elif lookup_type == "industry":
            result = data_lookup_service.search_industry_reports(**query)
        elif lookup_type == "web":
            result = data_lookup_service.search_web(**query)
        elif lookup_type == "company":
            result = data_lookup_service.lookup_company_data(**query)
        else:
            raise HTTPException(status_code=400, detail=f"Tipo de búsqueda no válido: {lookup_type}")
        
        return DataLookupResponse(
            success=True,
            result=result,
            lookup_type=lookup_type,
            query=query
        )
    
    except Exception as e:
        logger.error(f"Error en búsqueda de datos {request.lookup_type}: {str(e)}")
        return DataLookupResponse(
            success=False,
            result={},
            lookup_type=request.lookup_type,
            query=request.query,
            error=str(e)
        ) 
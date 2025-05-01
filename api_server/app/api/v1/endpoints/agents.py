import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.logging import logger
from app.core.metrics import MetricsCollector
from app.core.orchestrator import AgentOrchestrator

router = APIRouter()
orchestrator = AgentOrchestrator()

class AgentRequest(BaseModel):
    query: str
    content: str | None = None
    action_request: str | None = None
    metadata: dict[str, Any] | None = None

class AgentResponse(BaseModel):
    status: str
    agent_used: str
    confidence: float
    result: Any
    execution_time: float | None = None

class AgentInfo(BaseModel):
    name: str
    description: str

@router.post("/process", response_model=AgentResponse)
async def process_request(request: AgentRequest):
    """
    Procesa una solicitud a través del sistema de orquestación de agentes.

    Args:
        request: La solicitud con el query y datos adicionales

    Returns:
        AgentResponse con el resultado del procesamiento
    """
    try:
        logger.info(
            "Nueva solicitud recibida",
            extra={"request_data": request.dict()}
        )

        # Convertir solicitud a diccionario para el orquestador
        input_data = request.dict(exclude_unset=True)

        # Procesar la solicitud a través del orquestador
        start_time = time.time()
        result = await orchestrator.process_request(input_data)
        execution_time = time.time() - start_time

        # Añadir tiempo de ejecución al resultado
        result["execution_time"] = execution_time

        logger.info(
            "Solicitud procesada exitosamente",
            extra={
                "agent_used": result["agent_used"],
                "confidence": result["confidence"],
                "execution_time": execution_time
            }
        )

        return AgentResponse(**result)

    except Exception as e:
        logger.error(
            f"Error al procesar la solicitud: {str(e)}",
            extra={"request_data": request.dict()}
        )
        MetricsCollector.record_error("api", "request_processing_error")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la solicitud: {str(e)}"
        )

@router.get("/agents", response_model=list[AgentInfo])
async def list_agents():
    """
    Lista todos los agentes disponibles en el sistema.
    """
    agents = [
        AgentInfo(
            name="Router Agent",
            description="Agente que decide qué agente especializado debe manejar la solicitud"
        ),
        AgentInfo(
            name="Analysis Agent",
            description="Agente especializado en análisis detallado de datos y textos"
        ),
        AgentInfo(
            name="Action Agent",
            description="Agente especializado en realizar acciones específicas"
        ),
        AgentInfo(
            name="Summary Agent",
            description="Agente especializado en crear resúmenes concisos"
        )
    ]

    return agents

@router.get("/health")
async def agent_health():
    """
    Verifica el estado de salud del sistema de agentes.
    """
    try:
        # Realizar una verificación básica del orquestador
        health_status = {
            "status": "healthy",
            "agents": {
                "router": orchestrator.router_agent is not None,
                "analysis": orchestrator.analysis_agent is not None,
                "action": orchestrator.action_agent is not None,
                "summary": orchestrator.summary_agent is not None
            },
            "workflow": orchestrator.workflow is not None
        }

        return health_status

    except Exception as e:
        logger.error(f"Error en verificación de salud: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

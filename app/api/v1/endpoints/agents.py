from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.core.graph import AgentGraph

router = APIRouter()
agent_graph = AgentGraph()

class AgentRequest(BaseModel):
    query: str
    content: Optional[str] = None
    action_request: Optional[str] = None

class AgentResponse(BaseModel):
    result: Dict[str, Any]
    confidence: float
    agent_used: str

@router.post("/process", response_model=AgentResponse)
async def process_request(request: AgentRequest):
    """
    Procesa una solicitud a través del sistema de agentes.
    """
    try:
        # Preparar los datos de entrada
        input_data = {
            "query": request.query,
            "content": request.content,
            "action_request": request.action_request
        }
        
        # Ejecutar el grafo de agentes
        result = await agent_graph.execute(input_data)
        
        return AgentResponse(
            result=result["agent_output"],
            confidence=result["confidence"],
            agent_used=result["current_agent"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando la solicitud: {str(e)}"
        )

@router.get("/agents")
async def list_agents():
    """
    Lista todos los agentes disponibles en el sistema.
    """
    return {
        "agents": [
            {
                "name": "Router Agent",
                "description": "Agente que decide qué agente especializado debe manejar la solicitud"
            },
            {
                "name": "Analysis Agent",
                "description": "Agente especializado en análisis detallado de datos y textos"
            },
            {
                "name": "Action Agent",
                "description": "Agente especializado en realizar acciones específicas"
            },
            {
                "name": "Summary Agent",
                "description": "Agente especializado en crear resúmenes concisos"
            }
        ]
    } 
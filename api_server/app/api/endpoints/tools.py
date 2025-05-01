import time
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.core.logging import logger
from app.core.metrics import MetricsCollector
from app.tools.tool_registry import tool_registry

router = APIRouter()
metrics = MetricsCollector()

# Modelos para el endpoint
class ToolDetail(BaseModel):
    """Información detallada sobre una herramienta."""
    name: str
    description: str
    has_implementation: bool
    inputs: dict[str, Any] | None = None
    outputs: dict[str, Any] | None = None

class ToolRequest(BaseModel):
    """Solicitud para ejecutar una herramienta."""
    tool_name: str
    params: dict[str, Any]
    request_id: str | None = None

class ToolResponse(BaseModel):
    """Respuesta de la ejecución de una herramienta."""
    tool_name: str
    request_id: str
    result: dict[str, Any]
    success: bool
    error: str | None = None
    execution_time: float

@router.get("/", response_model=list[ToolDetail])
async def list_tools():
    """
    Lista todas las herramientas disponibles en el sistema.

    Returns:
        Lista de herramientas disponibles con detalles
    """
    tools = tool_registry.get_tool_details()

    # Agregar información de esquemas
    detailed_tools = []
    for tool in tools:
        schema = tool_registry.get_tool_schema(tool["name"])
        if schema:
            detailed_tools.append(
                ToolDetail(
                    name=tool["name"],
                    description=tool["description"],
                    has_implementation=tool["has_implementation"],
                    inputs=schema.get("inputs"),
                    outputs=schema.get("outputs")
                )
            )

    return detailed_tools

@router.get("/{tool_name}", response_model=ToolDetail)
async def get_tool_info(tool_name: str):
    """
    Obtiene información detallada sobre una herramienta específica.

    Args:
        tool_name: Nombre de la herramienta

    Returns:
        Detalles de la herramienta

    Raises:
        HTTPException: Si la herramienta no existe
    """
    schema = tool_registry.get_tool_schema(tool_name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Herramienta '{tool_name}' no encontrada")

    has_implementation = tool_name in tool_registry.list_tools_with_implementations()

    return ToolDetail(
        name=tool_name,
        description=schema.get("description", ""),
        has_implementation=has_implementation,
        inputs=schema.get("inputs"),
        outputs=schema.get("outputs")
    )

@router.post("/execute", response_model=ToolResponse)
async def execute_tool(request: ToolRequest, background_tasks: BackgroundTasks):
    """
    Ejecuta una herramienta específica con los parámetros proporcionados.

    Args:
        request: Solicitud con el nombre de la herramienta y los parámetros
        background_tasks: Tareas en segundo plano para métricas

    Returns:
        Resultado de la ejecución de la herramienta

    Raises:
        HTTPException: Si la herramienta no existe o no tiene implementación
    """
    # Generar ID de solicitud si no se proporciona
    request_id = request.request_id or str(uuid.uuid4())

    # Verificar que la herramienta existe
    tool_name = request.tool_name
    schema = tool_registry.get_tool_schema(tool_name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Herramienta '{tool_name}' no encontrada")

    # Verificar que la herramienta tiene implementación
    implementation = tool_registry.get_tool_implementation(tool_name)
    if not implementation:
        raise HTTPException(
            status_code=501,
            detail=f"La herramienta '{tool_name}' no tiene implementación"
        )

    # Ejecutar la herramienta
    start_time = time.time()
    logger.info(f"Ejecutando herramienta '{tool_name}' (request_id: {request_id})")

    try:
        # Llamar a la implementación de la herramienta
        result = await implementation(request.params) if callable(implementation) else implementation(request.params)

        # Calcular tiempo de ejecución
        execution_time = time.time() - start_time

        # Registrar métricas en segundo plano
        background_tasks.add_task(
            metrics.record_tool_execution,
            tool_name=tool_name,
            success=True,
            execution_time=execution_time
        )

        logger.info(f"Herramienta '{tool_name}' ejecutada con éxito en {execution_time:.4f}s (request_id: {request_id})")

        return ToolResponse(
            tool_name=tool_name,
            request_id=request_id,
            result=result,
            success=True,
            execution_time=execution_time
        )

    except Exception as e:
        # Calcular tiempo de ejecución en caso de error
        execution_time = time.time() - start_time
        error_msg = f"Error al ejecutar herramienta '{tool_name}': {str(e)}"

        # Registrar métricas en segundo plano
        background_tasks.add_task(
            metrics.record_tool_execution,
            tool_name=tool_name,
            success=False,
            execution_time=execution_time,
            error=str(e)
        )

        logger.error(f"{error_msg} (request_id: {request_id})")

        return ToolResponse(
            tool_name=tool_name,
            request_id=request_id,
            result={},
            success=False,
            error=str(e),
            execution_time=execution_time
        )

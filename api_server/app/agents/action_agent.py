import os
import time
from pathlib import Path
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.agents.base import BaseAgent
from app.core.config import get_settings
from app.core.logging import logger
from app.tools.mcp_client import MCPClient

# Obtener la configuración
settings = get_settings()

# Función para crear un LLM que puede ser reemplazado en los tests
def create_llm():
    return ChatOpenAI(
        model_name=settings.OPENAI_MODEL,
        temperature=settings.TEMPERATURE,
        api_key=settings.OPENAI_API_KEY,
    )

# LLM global que puede ser sustituido desde los tests
llm = create_llm()

class ActionAgent(BaseAgent):
    def __init__(self, model=None):
        super().__init__(
            name="action_agent",
            description="Agente especializado en realizar acciones específicas"
        )
        # Asignar el LLM importado a la propiedad de la instancia
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un agente especializado en realizar acciones específicas.
            Tu objetivo es ejecutar tareas concretas y proporcionar resultados tangibles.
            
            Debes:
            1. Identificar la acción requerida
            2. Planificar los pasos necesarios
            3. Ejecutar la acción de manera eficiente
            4. Proporcionar un reporte detallado del resultado
            
            Formatea tu respuesta incluyendo:
            - Acción realizada
            - Pasos ejecutados
            - Resultado obtenido
            - Recomendaciones posteriores"""),
            ("human", "{input}")
        ])
        # Inicializar cliente MCP
        mcp_path = str(Path(os.path.abspath(__file__)).parents[3] / "mcp_server" / "main.py")
        self.mcp_client = MCPClient(
            base_url=settings.MCP_CLIENT_URL,
            use_stdio=True,
            mcp_server_path=mcp_path
        )

    def _execute_impl(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta la acción solicitada."""
        start_time = time.time()

        # Extraer la consulta
        query = input_data.get("query", "")

        # Loguear la consulta con un límite seguro
        query_preview = query[:50] + "..." if len(query) > 50 else query
        logger.info(f"ActionAgent procesando consulta: {query_preview}")

        # Formatear el prompt correctamente
        formatted_prompt = self.prompt.format(input=query)

        # Llamar a la herramienta MCP 'query_kb'
        mcp_result = self.mcp_client.call_tool_sync("query_kb", {"query": query})
        processing_time = time.time() - start_time
        return {
            "action_result": mcp_result.get("result", ""),
            "input": input_data,
            "confidence": mcp_result.get("confidence", 0.0),
            "processing_time": processing_time
        }

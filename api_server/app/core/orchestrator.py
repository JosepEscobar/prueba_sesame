import time
import uuid
from typing import Any

from langchain_core.runnables import RunnableConfig

from app.core.graph import AgentGraph
from app.core.logging import logger
from app.core.metrics import MetricsCollector


class Orchestrator:
    """
    Orquestador del sistema multi-agente.

    Coordina el flujo de trabajo entre los diferentes agentes, gestionando el
    enrutamiento de consultas, ejecución de agentes especializados y la
    integración de los resultados.
    """

    def __init__(self):
        """Inicializa el orquestador con todos los agentes necesarios."""
        self.request_id = None

        # Inicializar el grafo de agentes
        self.agent_graph = AgentGraph()

        logger.info("Orchestrator inicializado con grafo de agentes y servicio de búsqueda de datos")

    def process_query(
        self, query: str, context: dict[str, Any] | None = None, agent_preference: str | None = None
    ) -> dict[str, Any]:
        """
        Procesa una consulta utilizando el sistema multi-agente.

        Args:
            query: Texto de la consulta
            context: Contexto adicional para enriquecer la consulta (opcional)
            agent_preference: Preferencia de agente específico (opcional)

        Returns:
            Resultado del procesamiento incluyendo agente utilizado, resultado y nivel de confianza
        """
        # Crear diccionario de solicitud
        request = {"query": query, "context": context or {}}

        if agent_preference:
            request["context"]["agent_preference"] = agent_preference

        # Procesar la solicitud
        result = self.process_request(request)

        # Adaptar el resultado al formato esperado por la API
        if result.get("status") == "success":
            return {
                "result": result["result"],
                "agent": result["selected_agent"],
                "confidence": result.get("confidence", 0.0),
                "processed_by": "summary_agent",  # Indicar que siempre pasa por el summary agent
                "processing_time": result.get("processing_time", 0.0),
            }
        else:
            # En caso de error, lanzar una excepción que será capturada en el router de la API
            raise Exception(result.get("error", "Error desconocido en el procesamiento de la consulta"))

    def process_request(self, request: dict[str, Any], request_id: str | None = None) -> dict[str, Any]:
        """
        Procesa una solicitud utilizando el sistema multi-agente.

        Args:
            request: Diccionario con los datos de la solicitud
            request_id: Identificador único para la solicitud (opcional)

        Returns:
            Resultado del procesamiento de la solicitud
        """
        # Generar o establecer ID de solicitud para rastreo
        self.request_id = request_id or str(uuid.uuid4())

        start_time = time.time()
        query = request.get("query", "")
        query_preview = query[:50] + "..." if len(query) > 50 else query
        logger.info(f"Procesando solicitud {self.request_id}: {query_preview}...")

        try:
            # Configurar contexto de ejecución con ID de solicitud para rastreo
            config = RunnableConfig(metadata={"request_id": self.request_id, "timestamp": time.time()})

            # Ejecutar el flujo completo usando el grafo de agentes
            graph_result = self.agent_graph.run({"query": query, "context": request.get("context", {})})

            # Añadir metadatos al resultado
            processing_time = time.time() - start_time
            result = {
                "status": "success",
                "result": graph_result["result"],
                "request_id": self.request_id,
                "processing_time": processing_time,
                "selected_agent": graph_result["agent"],
                "confidence": graph_result.get("confidence", 0.0),
            }

            logger.info(
                f"Solicitud {self.request_id} procesada exitosamente en {processing_time:.2f} segundos por {graph_result['agent']} y resumida por summary_agent"
            )
            return result

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error en procesamiento de solicitud: {str(e)}"
            logger.error(error_msg)
            MetricsCollector.record_error("orchestrator", "processing_error")

            return {
                "status": "error",
                "error": error_msg,
                "request_id": self.request_id,
                "processing_time": processing_time,
            }

    def get_available_agents(self) -> list[dict[str, Any]]:
        """
        Retorna una lista de agentes disponibles en el sistema.

        Returns:
            Lista de diccionarios con información de cada agente
        """
        return [
            {
                "id": "analysis",
                "name": "Analysis Agent",
                "description": "Agente especializado en análisis detallado de datos y textos",
            },
            {
                "id": "finance",
                "name": "Finance Agent",
                "description": "Especialista en finanzas, análisis financiero y estrategias de inversión",
            },
            {
                "id": "marketing",
                "name": "Marketing Agent",
                "description": "Especialista en marketing, análisis de mercado y estrategias comerciales",
            },
            {
                "id": "summary",
                "name": "Summary Agent",
                "description": "Especialista en síntesis de información y generación de resúmenes",
            },
        ]

    def get_agent_info(self, agent_id: str) -> dict[str, Any] | None:
        """
        Retorna información detallada sobre un agente específico.

        Args:
            agent_id: Identificador del agente

        Returns:
            Diccionario con información detallada del agente o None si no existe
        """
        if agent_id not in self.agents:
            return None

        agent = self.agents[agent_id]
        return {
            "id": agent_id,
            "name": agent.name,
            "description": getattr(agent, "description", "Agente especializado del sistema multi-agente"),
            "capabilities": getattr(agent, "capabilities", ["Procesamiento de consultas especializadas"]),
            "configuration": {
                "model": getattr(agent, "model_name", "default_model"),
                "tools": list(getattr(agent, "tools", {}).keys()),
            },
        }

    def get_system_stats(self) -> dict[str, Any]:
        """
        Retorna estadísticas del sistema multi-agente.

        Returns:
            Diccionario con estadísticas del sistema
        """
        # En una implementación real, estas estadísticas vendrían de un sistema
        # de monitoreo como Prometheus. Aquí se simula con datos estáticos.
        return {
            "uptime": time.time() - 1682341200,  # Tiempo desde un momento arbitrario
            "total_requests": 1250,
            "success_rate": 0.95,
            "average_response_time": 2.3,
            "agent_distribution": {
                "analysis_agent": 0.45,
                "action_agent": 0.25,
                "summary_agent": 0.15,
                "finance_agent": 0.10,
                "marketing_agent": 0.05,
            },
        }

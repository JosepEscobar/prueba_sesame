from typing import Dict, Any, List, Optional
import time
import uuid

from langchain_core.runnables import RunnableConfig

from app.core.logging import logger
from app.core.metrics import MetricsCollector
from app.agents.router_agent import RouterAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.action_agent import ActionAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.marketing_agent import MarketingAgent


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
        
        # Inicializar los agentes
        self.router = RouterAgent()
        
        # Inicializar agentes especializados
        self.agents = {
            "analysis_agent": AnalysisAgent(),
            "action_agent": ActionAgent(),
            "summary_agent": SummaryAgent(),
            "finance_agent": FinanceAgent(),
            "marketing_agent": MarketingAgent()
        }
        
        logger.info(f"Orchestrator inicializado con {len(self.agents)} agentes")
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una solicitud completa, desde el enrutamiento hasta la ejecución
        del agente especializado.
        
        Args:
            request: Diccionario con los datos de la solicitud, incluyendo 'query' y contexto
            
        Returns:
            Diccionario con los resultados del procesamiento
        """
        # Generar un ID único para la solicitud
        self.request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Extraer la consulta principal
        query = request.get("query", "")
        if not query:
            return {"error": "Se requiere una consulta ('query') en la solicitud", "success": False}
        
        logger.info(
            f"Iniciando procesamiento de solicitud #{self.request_id}", 
            extra={"request_id": self.request_id, "query": query[:100]}
        )
        
        try:
            # Configuración para pasar el request_id a los agentes
            config = RunnableConfig(
                metadata={"request_id": self.request_id}
            )
            
            # 1. Enrutar la solicitud al agente apropiado
            router_result = self.router._execute_impl(request)
            selected_agent_name = router_result.get("agent")
            
            logger.info(
                f"Router seleccionó {selected_agent_name}", 
                extra={"request_id": self.request_id, "selected_agent": selected_agent_name}
            )
            
            # 2. Verificar que el agente existe
            if selected_agent_name not in self.agents:
                logger.error(
                    f"Agente '{selected_agent_name}' no encontrado en el sistema", 
                    extra={"request_id": self.request_id}
                )
                return {"error": f"Agente '{selected_agent_name}' no disponible", "success": False}
            
            # 3. Ejecutar el agente seleccionado
            selected_agent = self.agents[selected_agent_name]
            
            logger.info(
                f"Ejecutando agente {selected_agent_name}", 
                extra={"request_id": self.request_id, "agent": selected_agent_name}
            )
            
            agent_result = selected_agent._execute_impl(request)
            
            # 4. Preparar la respuesta final
            processing_time = time.time() - start_time
            
            # Registrar métricas
            MetricsCollector.record_agent_execution(
                agent_name="orchestrator",
                execution_time=processing_time,
                status="success"
            )
            
            logger.info(
                f"Solicitud #{self.request_id} procesada con éxito en {processing_time:.2f} segundos", 
                extra={"request_id": self.request_id, "processing_time": processing_time}
            )
            
            # Combinar los resultados para la respuesta final
            final_response = {
                "result": agent_result.get("analysis", agent_result),
                "agent_used": selected_agent_name,
                "processing_time": processing_time,
                "request_id": self.request_id,
                "success": True
            }
            
            # Añadir fuentes de datos si están disponibles
            if "data_sources" in agent_result:
                final_response["sources"] = agent_result["data_sources"]
            
            return final_response
            
        except Exception as e:
            # Registrar el error
            processing_time = time.time() - start_time
            logger.error(
                f"Error al procesar solicitud #{self.request_id}: {str(e)}", 
                extra={"request_id": self.request_id, "error": str(e)}
            )
            
            # Registrar métricas de error
            MetricsCollector.record_agent_execution(
                agent_name="orchestrator",
                execution_time=processing_time,
                status="error"
            )
            
            MetricsCollector.record_error(
                agent_name="orchestrator",
                error_type=type(e).__name__
            )
            
            return {
                "error": f"Error al procesar la solicitud: {str(e)}",
                "request_id": self.request_id,
                "success": False
            } 
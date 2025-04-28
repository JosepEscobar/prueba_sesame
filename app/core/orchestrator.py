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
from app.services.data_lookup import DataLookupService


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
        
        # Inicializar servicio de búsqueda de datos
        self.data_lookup_service = DataLookupService()
        
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
        
        # Proporcionar el servicio de búsqueda a todos los agentes
        for agent in self.agents.values():
            agent.add_tool("data_lookup", self.data_lookup_service)
        
        logger.info(f"Orchestrator inicializado con {len(self.agents)} agentes y servicio de búsqueda de datos")
    
    def process_request(self, request: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
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
        logger.info(f"Procesando solicitud {self.request_id}: {request.get('query', '')[:50]}...")
        
        try:
            # Configurar contexto de ejecución con ID de solicitud para rastreo
            config = RunnableConfig(
                metadata={
                    "request_id": self.request_id,
                    "timestamp": time.time()
                }
            )
            
            # Ejecutar el agente router para determinar qué agente especializado usar
            router_result = self.router.execute(request)
            
            if "error" in router_result:
                logger.error(f"Error en router: {router_result['error']}")
                MetricsCollector.record_error("router_agent", "routing_error")
                return {
                    "status": "error",
                    "error": router_result["error"],
                    "request_id": self.request_id,
                    "processing_time": time.time() - start_time
                }
            
            # Obtener el agente seleccionado
            selected_agent_name = router_result.get("agent", "")
            confidence = router_result.get("confidence", 0)
            
            logger.info(f"Router seleccionó agente '{selected_agent_name}' con confianza {confidence}")
            
            if selected_agent_name not in self.agents:
                error_msg = f"Agente seleccionado '{selected_agent_name}' no está disponible"
                logger.error(error_msg)
                MetricsCollector.record_error("orchestrator", "agent_not_found")
                return {
                    "status": "error",
                    "error": error_msg,
                    "request_id": self.request_id,
                    "processing_time": time.time() - start_time
                }
            
            # Ejecutar el agente seleccionado
            selected_agent = self.agents[selected_agent_name]
            agent_result = selected_agent.execute(router_result.get("input", request))
            
            # Verificar si se necesita un resumen
            final_result = agent_result
            if router_result.get("needs_summary", False) and "result" in agent_result:
                logger.info("Generando resumen final del resultado")
                summary_input = {
                    "query": request.get("query", ""),
                    "context": agent_result["result"]
                }
                summary_result = self.agents["summary_agent"].execute(summary_input)
                final_result = {
                    "original_result": agent_result["result"],
                    "summary": summary_result["result"],
                    "confidence": summary_result.get("confidence", 0)
                }
            
            # Añadir metadatos al resultado
            processing_time = time.time() - start_time
            result = {
                "status": "success",
                "result": final_result,
                "request_id": self.request_id,
                "processing_time": processing_time,
                "selected_agent": selected_agent_name
            }
            
            logger.info(f"Solicitud {self.request_id} procesada exitosamente en {processing_time:.2f} segundos")
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
                "processing_time": processing_time
            } 
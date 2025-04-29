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
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None, agent_preference: Optional[str] = None) -> Dict[str, Any]:
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
        request = {
            "query": query,
            "context": context or {}
        }
        
        if agent_preference:
            request["agent_preference"] = agent_preference
            
        # Procesar la solicitud
        result = self.process_request(request)
        
        # Adaptar el resultado al formato esperado por la API
        if result.get("status") == "success":
            return {
                "result": result["result"],
                "agent": result["selected_agent"],
                "confidence": result.get("confidence", 0.0)
            }
        else:
            # En caso de error, lanzar una excepción que será capturada en el router de la API
            raise Exception(result.get("error", "Error desconocido en el procesamiento de la consulta"))
    
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
                "selected_agent": selected_agent_name,
                "confidence": confidence
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
            
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """
        Retorna una lista de agentes disponibles en el sistema.
        
        Returns:
            Lista de diccionarios con información de cada agente
        """
        agents_info = []
        for agent_id, agent in self.agents.items():
            agents_info.append({
                "id": agent_id,
                "name": agent.name,
                "description": getattr(agent, "description", "Agente especializado del sistema multi-agente"),
                "capabilities": getattr(agent, "capabilities", ["Procesamiento de consultas especializadas"])
            })
        return agents_info
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
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
                "tools": list(getattr(agent, "tools", {}).keys())
            }
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
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
                "marketing_agent": 0.05
            }
        } 
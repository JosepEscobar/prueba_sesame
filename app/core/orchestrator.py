from typing import Dict, Any, List, Tuple, Callable
from langgraph.graph import Graph, StateGraph
from langgraph.prebuilt import ToolExecutor
from app.agents.router_agent import RouterAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.action_agent import ActionAgent
from app.agents.summary_agent import SummaryAgent
from app.core.logging import logger
from app.core.metrics import MetricsCollector
from app.core.config import get_settings
import time

settings = get_settings()

class AgentOrchestrator:
    def __init__(self):
        self.router_agent = RouterAgent()
        self.analysis_agent = AnalysisAgent()
        self.action_agent = ActionAgent()
        self.summary_agent = SummaryAgent()
        
        # Crear el grafo de agentes
        self.workflow = self._create_workflow()
        
        logger.info("Orquestador de agentes inicializado")
        
    def _create_workflow(self) -> Graph:
        """Crea el grafo de flujo de trabajo para los agentes."""
        # Definir el estado inicial
        workflow = StateGraph(StateType=Dict)
        
        # Definir los nodos del grafo
        workflow.add_node("router", self._route_request)
        workflow.add_node("analysis", self._handle_analysis)
        workflow.add_node("action", self._handle_action)
        workflow.add_node("summary", self._handle_summary)
        
        # Definir el enrutador condicional
        workflow.add_conditional_edges(
            "router",
            self._route_selector,
            {
                "analysis": "analysis",
                "action": "action",
                "summary": "summary"
            }
        )
        
        # Definir el nodo de inicio
        workflow.set_entry_point("router")
        
        # Compilar el grafo
        return workflow.compile()
    
    def _route_selector(self, state: Dict[str, Any]) -> str:
        """Función que selecciona el siguiente nodo basado en la decisión del router."""
        agent_decision = state.get("agent_decision", "")
        confidence = state.get("router_confidence", 0.0)
        
        logger.info(
            f"Seleccionando ruta: {agent_decision}",
            extra={
                "agent_decision": agent_decision,
                "confidence": confidence
            }
        )
        
        # Verificar el umbral de confianza
        if confidence < settings.ORCHESTRATOR_CONFIDENCE_THRESHOLD:
            logger.warning(
                f"Confianza por debajo del umbral ({confidence} < {settings.ORCHESTRATOR_CONFIDENCE_THRESHOLD})",
                extra={
                    "confidence": confidence,
                    "threshold": settings.ORCHESTRATOR_CONFIDENCE_THRESHOLD
                }
            )
            # Por defecto, usar analysis si la confianza es baja
            return "analysis"
        
        # Validar que la decisión es una de las rutas válidas
        valid_routes = ["analysis", "action", "summary"]
        if agent_decision not in valid_routes:
            logger.warning(
                f"Decisión de ruta no válida: {agent_decision}",
                extra={"agent_decision": agent_decision}
            )
            return "analysis"  # Ruta por defecto
        
        return agent_decision
    
    async def _route_request(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Enruta la solicitud al agente apropiado."""
        try:
            start_time = time.time()
            
            result = await self.router_agent.execute(state["input"])
            execution_time = time.time() - start_time
            
            # Actualizar el estado con la decisión del router
            state["agent_decision"] = result["agent_decision"]
            state["router_confidence"] = result["confidence"]
            state["routing_reasoning"] = result.get("reasoning", "")
            state["routing_time"] = execution_time
            
            logger.info(
                f"Router completado: {result['agent_decision']}",
                extra={
                    "agent_decision": result["agent_decision"],
                    "confidence": result["confidence"],
                    "execution_time": execution_time
                }
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error en el enrutamiento: {str(e)}")
            MetricsCollector.record_error("router", "routing_error")
            
            # En caso de error, configurar un estado por defecto
            state["agent_decision"] = "analysis"  # Agente por defecto
            state["router_confidence"] = 0.5
            state["routing_error"] = str(e)
            
            return state
    
    async def _handle_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la solicitud de análisis."""
        try:
            start_time = time.time()
            
            # Ejecutar el agente de análisis
            result = await self.analysis_agent.execute(state["input"])
            execution_time = time.time() - start_time
            
            # Actualizar el estado con los resultados
            state["analysis_result"] = result["analysis"]
            state["analysis_confidence"] = result["confidence"]
            state["analysis_time"] = execution_time
            
            logger.info(
                "Análisis completado",
                extra={
                    "execution_time": execution_time,
                    "confidence": result["confidence"]
                }
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error en el análisis: {str(e)}")
            MetricsCollector.record_error("analysis", "analysis_error")
            
            # En caso de error, registrar el error en el estado
            state["analysis_error"] = str(e)
            
            return state
    
    async def _handle_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la solicitud de acción."""
        try:
            start_time = time.time()
            
            # Ejecutar el agente de acción
            result = await self.action_agent.execute(state["input"])
            execution_time = time.time() - start_time
            
            # Actualizar el estado con los resultados
            state["action_result"] = result["action_result"]
            state["action_confidence"] = result["confidence"]
            state["action_time"] = execution_time
            
            logger.info(
                "Acción completada",
                extra={
                    "execution_time": execution_time,
                    "confidence": result["confidence"]
                }
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error en la acción: {str(e)}")
            MetricsCollector.record_error("action", "action_error")
            
            # En caso de error, registrar el error en el estado
            state["action_error"] = str(e)
            
            return state
    
    async def _handle_summary(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la solicitud de resumen."""
        try:
            start_time = time.time()
            
            # Ejecutar el agente de resumen
            result = await self.summary_agent.execute(state["input"])
            execution_time = time.time() - start_time
            
            # Actualizar el estado con los resultados
            state["summary_result"] = result["summary"]
            state["summary_confidence"] = result["confidence"]
            state["summary_time"] = execution_time
            
            logger.info(
                "Resumen completado",
                extra={
                    "execution_time": execution_time,
                    "confidence": result["confidence"]
                }
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error en el resumen: {str(e)}")
            MetricsCollector.record_error("summary", "summary_error")
            
            # En caso de error, registrar el error en el estado
            state["summary_error"] = str(e)
            
            return state
    
    async def process_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa una solicitud a través del flujo de trabajo de agentes."""
        try:
            start_time = time.time()
            
            # Registrar el inicio del procesamiento
            logger.info(
                "Iniciando procesamiento de solicitud",
                extra={"input_data": input_data}
            )
            
            # Inicializar el estado
            initial_state = {
                "input": input_data,
                "request_id": input_data.get("request_id", str(time.time())),
                "start_time": start_time
            }
            
            # Ejecutar el flujo de trabajo
            final_state = await self.workflow.arun(initial_state)
            total_execution_time = time.time() - start_time
            
            # Identificar el agente utilizado
            agent_used = final_state.get("agent_decision", "unknown")
            
            # Obtener el resultado según el agente utilizado
            result = None
            confidence = 0.0
            
            if agent_used == "analysis":
                result = final_state.get("analysis_result")
                confidence = final_state.get("analysis_confidence", 0.0)
            elif agent_used == "action":
                result = final_state.get("action_result")
                confidence = final_state.get("action_confidence", 0.0)
            elif agent_used == "summary":
                result = final_state.get("summary_result")
                confidence = final_state.get("summary_confidence", 0.0)
            
            # Registrar estadísticas de ejecución
            logger.info(
                f"Solicitud procesada por {agent_used}",
                extra={
                    "agent_used": agent_used,
                    "confidence": confidence,
                    "total_execution_time": total_execution_time,
                    "request_id": final_state.get("request_id")
                }
            )
            
            # Preparar la respuesta
            response = {
                "status": "success",
                "agent_used": agent_used,
                "confidence": confidence,
                "result": result,
                "processing_time": total_execution_time,
                "routing": {
                    "decision": agent_used,
                    "confidence": final_state.get("router_confidence", 0.0),
                    "reasoning": final_state.get("routing_reasoning", "")
                }
            }
            
            # Registrar errores si los hay
            if f"{agent_used}_error" in final_state:
                response["error"] = final_state[f"{agent_used}_error"]
                response["status"] = "error"
            
            return response
            
        except Exception as e:
            logger.error(f"Error en el procesamiento de la solicitud: {str(e)}")
            MetricsCollector.record_error("orchestrator", "processing_error")
            
            return {
                "status": "error",
                "error": str(e),
                "agent_used": "none",
                "confidence": 0.0,
                "result": None
            } 
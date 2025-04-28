from typing import Dict, Any, List, Tuple
from langgraph.graph import Graph, StateGraph
from langgraph.prebuilt import ToolExecutor
from app.agents.router_agent import RouterAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.action_agent import ActionAgent
from app.agents.summary_agent import SummaryAgent
from app.core.logging import logger
from app.core.metrics import MetricsCollector

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
        
        # Definir las transiciones
        workflow.add_edge("router", "analysis")
        workflow.add_edge("router", "action")
        workflow.add_edge("router", "summary")
        
        # Definir el nodo de inicio
        workflow.set_entry_point("router")
        
        return workflow.compile()
    
    async def _route_request(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Enruta la solicitud al agente apropiado."""
        try:
            result = await self.router_agent.execute(state)
            agent_decision = result["agent_decision"].lower()
            
            # Actualizar el estado con la decisión del router
            state["agent_decision"] = agent_decision
            state["router_confidence"] = result["confidence"]
            
            return state
            
        except Exception as e:
            logger.error(f"Error en el enrutamiento: {str(e)}")
            MetricsCollector.record_error("router", "routing_error")
            raise
    
    async def _handle_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la solicitud de análisis."""
        try:
            result = await self.analysis_agent.execute(state)
            state["analysis_result"] = result["analysis"]
            state["analysis_confidence"] = result["confidence"]
            return state
            
        except Exception as e:
            logger.error(f"Error en el análisis: {str(e)}")
            MetricsCollector.record_error("analysis", "analysis_error")
            raise
    
    async def _handle_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la solicitud de acción."""
        try:
            result = await self.action_agent.execute(state)
            state["action_result"] = result["action_result"]
            state["action_confidence"] = result["confidence"]
            return state
            
        except Exception as e:
            logger.error(f"Error en la acción: {str(e)}")
            MetricsCollector.record_error("action", "action_error")
            raise
    
    async def _handle_summary(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja la solicitud de resumen."""
        try:
            result = await self.summary_agent.execute(state)
            state["summary_result"] = result["summary"]
            state["summary_confidence"] = result["confidence"]
            return state
            
        except Exception as e:
            logger.error(f"Error en el resumen: {str(e)}")
            MetricsCollector.record_error("summary", "summary_error")
            raise
    
    async def process_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa una solicitud a través del flujo de trabajo de agentes."""
        try:
            # Inicializar el estado
            initial_state = {
                "input": input_data,
                "agent_decision": None,
                "router_confidence": None,
                "analysis_result": None,
                "analysis_confidence": None,
                "action_result": None,
                "action_confidence": None,
                "summary_result": None,
                "summary_confidence": None
            }
            
            # Ejecutar el flujo de trabajo
            final_state = await self.workflow.arun(initial_state)
            
            # Preparar la respuesta
            response = {
                "status": "success",
                "agent_used": final_state["agent_decision"],
                "confidence": final_state.get(f"{final_state['agent_decision']}_confidence"),
                "result": final_state.get(f"{final_state['agent_decision']}_result")
            }
            
            logger.info(
                "Solicitud procesada exitosamente",
                extra={
                    "agent_used": final_state["agent_decision"],
                    "confidence": response["confidence"]
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error en el procesamiento de la solicitud: {str(e)}")
            MetricsCollector.record_error("orchestrator", "processing_error")
            raise 
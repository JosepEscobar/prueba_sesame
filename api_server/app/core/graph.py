from typing import Dict, Any, List, TypedDict
from langgraph.graph import Graph, StateGraph
from app.agents.router_agent import RouterAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.action_agent import ActionAgent
from app.agents.summary_agent import SummaryAgent
from app.core.logging import logger

class AgentState(TypedDict):
    messages: List[str]
    current_agent: str
    agent_output: Dict[str, Any]
    confidence: float

class AgentGraph:
    def __init__(self):
        self.router = RouterAgent()
        self.analysis = AnalysisAgent()
        self.action = ActionAgent()
        self.summary = SummaryAgent()
        self.graph = self._build_graph()
        logger.info("AgentGraph inicializado con 4 agentes")
        
    def _build_graph(self) -> Graph:
        """Construye el grafo de agentes."""
        # Crear el grafo
        workflow = StateGraph(AgentState)
        
        # Añadir nodos
        workflow.add_node("router", self.router.execute)
        workflow.add_node("analysis", self.analysis.execute)
        workflow.add_node("action", self.action.execute)
        workflow.add_node("summary", self.summary.execute)
        
        # Definir las transiciones
        def route_to_agent(state: AgentState) -> str:
            """Determina el siguiente agente basado en la decisión del router."""
            agent_output = state["agent_output"]
            selected_agent = agent_output.get("agent", "")
            
            logger.info(f"Enrutando solicitud a: {selected_agent}")
            
            if selected_agent == "analysis_agent":
                return "analysis"
            elif selected_agent == "action_agent":
                return "action"
            elif selected_agent == "summary_agent":
                return "summary"
            else:
                logger.warning(f"Agente desconocido: {selected_agent}, finalizando flujo")
                return "end"
                
        def should_continue(state: AgentState) -> str:
            """Determina si continuar o terminar."""
            confidence = state.get("confidence", 0)
            agent_output = state.get("agent_output", {})
            
            if "error" in agent_output:
                logger.warning(f"Error detectado en la ejecución del agente: {agent_output.get('error')}")
                return "end"
            
            if confidence > 0.7:
                logger.info(f"Confianza suficiente ({confidence}), volviendo al router")
                return "router"
            
            logger.info(f"Confianza insuficiente ({confidence}), finalizando flujo")
            return "end"
            
        # Añadir las transiciones
        workflow.add_edge("router", route_to_agent)
        workflow.add_edge("analysis", should_continue)
        workflow.add_edge("action", should_continue)
        workflow.add_edge("summary", should_continue)
        
        # Establecer el nodo de entrada
        workflow.set_entry_point("router")
        
        logger.info("Grafo de agentes construido correctamente")
        return workflow.compile()
        
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta el flujo de agentes sobre los datos de entrada.
        
        Args:
            input_data: Datos de entrada para el flujo de agentes
            
        Returns:
            Resultado final del flujo de agentes
        """
        try:
            # Loguear la consulta con un límite seguro
            query = input_data.get('query', '')
            query_preview = query[:50] + "..." if len(query) > 50 else query
            logger.info(f"Iniciando ejecución del grafo de agentes con input: {query_preview}")
            
            # Configurar el estado inicial
            state = {
                "messages": [input_data.get("query", "")],
                "current_agent": "router",
                "agent_output": {"input": input_data},
                "confidence": 1.0  # Confianza inicial
            }
            
            # Ejecutar el flujo
            result = self.graph.invoke(state)
            
            # Extraer y devolver la salida final
            final_output = result.get("agent_output", {})
            logger.info("Ejecución del grafo de agentes completada con éxito")
            
            return final_output
            
        except Exception as e:
            logger.error(f"Error en ejecución del grafo de agentes: {str(e)}")
            return {
                "error": f"Error en el flujo de agentes: {str(e)}",
                "input": input_data.get("query", "")
            } 
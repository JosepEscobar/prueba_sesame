from typing import Dict, Any, List, TypedDict
from langgraph.graph import Graph, StateGraph
from app.agents.router_agent import RouterAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.action_agent import ActionAgent
from app.agents.summary_agent import SummaryAgent

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
            decision = state["agent_output"].get("agent_decision", "").lower()
            
            if "análisis" in decision or "analysis" in decision:
                return "analysis"
            elif "acción" in decision or "action" in decision:
                return "action"
            elif "resumen" in decision or "summary" in decision:
                return "summary"
            else:
                return "end"
                
        def should_continue(state: AgentState) -> str:
            """Determina si continuar o terminar."""
            if state["confidence"] > 0.7:
                return "router"
            return "end"
            
        # Añadir las transiciones
        workflow.add_edge("router", route_to_agent)
        workflow.add_edge("analysis", should_continue)
        workflow.add_edge("action", should_continue)
        workflow.add_edge("summary", should_continue)
        
        # Establecer el nodo de entrada
        workflow.set_entry_point("router")
        
        return workflow.compile()
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el grafo de agentes."""
        initial_state = {
            "messages": [],
            "current_agent": "router",
            "agent_output": {},
            "confidence": 1.0
        }
        
        # Ejecutar el grafo
        final_state = await self.graph.ainvoke(initial_state)
        
        return final_state 
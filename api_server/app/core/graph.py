from typing import Dict, Any, List, TypedDict, Literal, Union
from langgraph.graph import Graph, StateGraph, END
from app.agents.router_agent import RouterAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.marketing_agent import MarketingAgent
from app.agents.summary_agent import SummaryAgent
from app.core.logging import logger

class AgentState(TypedDict):
    query: str
    context: Dict[str, Any]
    agent_output: Dict[str, Any]
    current_agent: str
    raw_response: str  # Añadimos un campo para la respuesta sin procesar

class AgentGraph:
    def __init__(self):
        self.router = RouterAgent()
        self.finance = FinanceAgent()
        self.marketing = MarketingAgent()
        self.analysis = AnalysisAgent()
        self.summary = SummaryAgent()
        self.graph = self._build_graph()
        logger.info("AgentGraph inicializado con 5 agentes incluyendo SummaryAgent")
        
    def _build_graph(self) -> Graph:
        """Construye el grafo de agentes."""
        workflow = StateGraph(AgentState)
        
        # Añadir nodos
        workflow.add_node("router", self._route)
        workflow.add_node("finance", self._process_finance)
        workflow.add_node("marketing", self._process_marketing)
        workflow.add_node("analysis", self._process_analysis)
        workflow.add_node("summary", self._process_summary)  # Nodo para el SummaryAgent
        
        # Definir transiciones
        workflow.add_conditional_edges(
            "router",
            self._decide_agent,
            {
                "finance": "finance",
                "marketing": "marketing",
                "analysis": "analysis",
                END: END
            }
        )
        
        # Todos los agentes especializados van al summary para procesamiento final
        workflow.add_edge("finance", "summary")
        workflow.add_edge("marketing", "summary")
        workflow.add_edge("analysis", "summary")
        
        # Solo el summary termina el flujo
        workflow.add_edge("summary", END)
        
        # Establecer nodo de entrada
        workflow.set_entry_point("router")
        
        logger.info("Grafo de agentes construido con flujo obligatorio por SummaryAgent")
        
        # Compilar el grafo
        compiled_graph = workflow.compile()
        logger.info("Grafo compilado exitosamente")
        return compiled_graph
        
    def _route(self, state: AgentState) -> AgentState:
        """
        Enruta la consulta al agente adecuado.
        """
        query = state["query"]
        context = state.get("context", {})
        
        logger.info(f"Router procesando consulta: {query[:50] if isinstance(query, str) else str(query)[:50]}...")
        result = self.router.execute({"query": query, "context": context})
        
        # Actualizar el estado
        state["current_agent"] = result.get("agent", "analysis")
        return state
    
    def _decide_agent(self, state: AgentState) -> str:
        """
        Determina qué agente debe procesar la consulta.
        """
        agent_name = state["current_agent"]
        
        # Mapeo de nombres de agentes devueltos por el router a los nodos del grafo
        agent_mapping = {
            "finance_agent": "finance",
            "marketing_agent": "marketing",
            "analysis_agent": "analysis"
        }
        
        # Si el nombre contiene _agent, obtener la versión simplificada para el grafo
        if agent_name in agent_mapping:
            return agent_mapping[agent_name]
        
        # Si el agente ya tiene el nombre correcto para el grafo, devolverlo directamente
        if agent_name in ["finance", "marketing", "analysis"]:
            return agent_name
            
        # Por defecto, usar análisis
        return "analysis"
    
    def _process_finance(self, state: AgentState) -> AgentState:
        """
        Procesa la consulta con el agente financiero.
        """
        query = state["query"]
        context = state.get("context", {})
        
        logger.info(f"Agente financiero procesando consulta: {query[:50] if isinstance(query, str) else str(query)[:50]}...")
        result = self.finance.execute({"query": query, "context": context})
        
        # Guardar la respuesta completa para summary
        if isinstance(result.get("result"), dict) and "content" in result["result"]:
            state["raw_response"] = result["result"]["content"]
        elif isinstance(result.get("result"), str):
            state["raw_response"] = result["result"]
        else:
            state["raw_response"] = str(result)
            
        state["agent_output"] = result
        return state
    
    def _process_marketing(self, state: AgentState) -> AgentState:
        """
        Procesa la consulta con el agente de marketing.
        """
        query = state["query"]
        context = state.get("context", {})
        
        logger.info(f"Agente de marketing procesando consulta: {query[:50] if isinstance(query, str) else str(query)[:50]}...")
        result = self.marketing.execute({"query": query, "context": context})
        
        # Guardar la respuesta completa para summary
        if isinstance(result.get("result"), dict) and "content" in result["result"]:
            state["raw_response"] = result["result"]["content"]
        elif isinstance(result.get("result"), str):
            state["raw_response"] = result["result"]
        else:
            state["raw_response"] = str(result)
            
        state["agent_output"] = result
        return state
    
    def _process_analysis(self, state: AgentState) -> AgentState:
        """
        Procesa la consulta con el agente de análisis.
        """
        query = state["query"]
        context = state.get("context", {})
        
        logger.info(f"Agente de análisis procesando consulta: {query[:50] if isinstance(query, str) else str(query)[:50]}...")
        result = self.analysis.execute({"query": query, "context": context})
        
        # Guardar la respuesta completa para summary
        if isinstance(result.get("result"), dict) and "content" in result["result"]:
            state["raw_response"] = result["result"]["content"]
        elif isinstance(result.get("result"), str):
            state["raw_response"] = result["result"]
        else:
            state["raw_response"] = str(result)
            
        state["agent_output"] = result
        return state
    
    def _process_summary(self, state: AgentState) -> AgentState:
        """
        Procesa el resultado con el agente de resumen.
        """
        query = state["query"]
        raw_response = state.get("raw_response", "")
        
        logger.info(f"Agente de resumen procesando resultado para consulta: {query[:50] if isinstance(query, str) else str(query)[:50]}...")
        
        # Crear contexto con la respuesta completa para el summary
        summary_context = {
            "content": raw_response,
            "source": state["current_agent"],
            "original_query": query
        }
        
        # Ejecutar el agente de resumen
        try:
            summary_result = self.summary.execute({
                "query": query,
                "context": summary_context
            })
            
            # Actualizar el estado con el resultado procesado
            if isinstance(summary_result.get("result"), dict):
                state["agent_output"] = summary_result["result"]
            else:
                state["agent_output"] = {
                    "content": summary_result.get("result", ""),
                    "source": state["current_agent"],
                    "summarized": True,
                    "original_response": raw_response
                }
        except Exception as e:
            logger.error(f"Error al procesar resumen: {str(e)}")
            # Proporcionar un resultado alternativo en caso de error
            state["agent_output"] = {
                "content": "",
                "source": state["current_agent"],
                "summarized": True,
                "original_response": raw_response
            }
        
        return state
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta el flujo completo para una consulta.
        
        Args:
            input_data: Diccionario con la consulta y contexto
            
        Returns:
            Resultado del procesamiento
        """
        query = input_data.get("query", "")
        context = input_data.get("context", {})
        
        initial_state = {
            "query": query,
            "context": context,
            "agent_output": {},
            "current_agent": "",
            "raw_response": ""
        }
        
        logger.info(f"Iniciando flujo de procesamiento para consulta: {query[:50] if isinstance(query, str) else str(query)[:50]}...")
        
        # Ejecutar el grafo
        final_state = self.graph.invoke(initial_state)
        
        # Procesar el resultado final
        result = {
            "result": final_state["agent_output"],
            "agent": final_state["current_agent"],
            "processed_by": "summary_agent",
            "confidence": 0.9
        }
        
        return result 
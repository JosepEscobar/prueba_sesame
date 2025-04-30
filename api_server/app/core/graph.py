from typing import Dict, Any, List, TypedDict, Literal, Union
from langgraph.graph import Graph, StateGraph, END
from app.agents.router_agent import RouterAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.marketing_agent import MarketingAgent
from app.core.logging import logger

class AgentState(TypedDict):
    query: str
    context: Dict[str, Any]
    agent_output: Dict[str, Any]
    current_agent: str

class AgentGraph:
    def __init__(self):
        self.router = RouterAgent()
        self.finance = FinanceAgent()
        self.marketing = MarketingAgent()
        self.analysis = AnalysisAgent()
        self.graph = self._build_graph()
        logger.info("AgentGraph inicializado con 4 agentes")
        
    def _build_graph(self) -> Graph:
        """Construye el grafo de agentes."""
        workflow = StateGraph(AgentState)
        
        # Añadir nodos
        workflow.add_node("router", self._route)
        workflow.add_node("finance", self._process_finance)
        workflow.add_node("marketing", self._process_marketing)
        workflow.add_node("analysis", self._process_analysis)
        
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
        
        # Todos los agentes específicos terminan el flujo
        workflow.add_edge("finance", END)
        workflow.add_edge("marketing", END)
        workflow.add_edge("analysis", END)
        
        # Establecer nodo de entrada
        workflow.set_entry_point("router")
        
        logger.info("Grafo de agentes construido correctamente")
        
        # Compilar el grafo
        compiled_graph = workflow.compile()
        logger.info("Grafo compilado exitosamente")
        return compiled_graph
    
    def _route(self, state: AgentState) -> AgentState:
        """Función del nodo router que clasifica la consulta."""
        query = state["query"]
        context = state["context"]
        
        input_data = {
            "query": query,
            "context": context
        }
        
        try:
            result = self.router.execute(input_data)
            logger.info(f"Router procesó la consulta exitosamente")
            
            # Imprimir para depuración
            print(f"*** RESULTADO DEL ROUTER AGENT: {result} ***")
            
            # Crear un nuevo estado con los resultados del router
            updated_state = state.copy()
            updated_state["agent_output"] = result
            updated_state["current_agent"] = "router"
            
            # Imprimir para depuración
            print(f"*** ESTADO ACTUALIZADO EN _route: {updated_state} ***")
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error en el router: {str(e)}")
            error_state = state.copy()
            error_state["agent_output"] = {"error": str(e)}
            error_state["current_agent"] = "router"
            return error_state
    
    def _decide_agent(self, state: AgentState) -> Union[Literal["finance", "marketing", "analysis"], type(END)]:
        """Decide qué agente debe procesar la consulta basándose en la clasificación del router."""
        agent_output = state.get("agent_output", {})
        
        # Imprimir para depuración
        print(f"*** ESTADO RECIBIDO EN _decide_agent: {state} ***")
        print(f"*** AGENT_OUTPUT EN _decide_agent: {agent_output} ***")
        
        # Verificar si hay errores
        if "error" in agent_output:
            logger.warning(f"Error encontrado en agent_output: {agent_output['error']}")
            return END
            
        # Caso especial: si agent_output está vacío pero hay una query, podemos intentar
        # reclasificar la consulta nosotros mismos
        if not agent_output and "query" in state:
            query = state["query"]
            logger.warning(f"agent_output vacío, intentando clasificar la consulta: {query[:50]}")
            
            # Llamar al router directamente
            try:
                router_result = self.router.execute({"query": query, "context": state.get("context", {})})
                agent_output = router_result  # Usar el resultado del router
                
                # Imprimir para depuración
                print(f"*** RECLASIFICACIÓN DEL ROUTER: {router_result} ***")
                
                # Actualizar el estado
                state["agent_output"] = router_result
            except Exception as e:
                logger.error(f"Error al reclasificar consulta: {str(e)}")
                return END
        
        # Intentar acceder al tipo de agente de diferentes maneras
        agent_type = None
        
        # 1. Método estándar - buscar en agent_output["agent"]
        if "agent" in agent_output:
            agent_type = agent_output["agent"]
            logger.info(f"Tipo de agente encontrado en agent_output['agent']: {agent_type}")
        
        # 2. Verificar si tenemos agent_type en input
        elif "input" in agent_output and isinstance(agent_output["input"], dict) and "agent_preference" in agent_output["input"]:
            agent_type = agent_output["input"]["agent_preference"]
            logger.info(f"Tipo de agente encontrado en agent_output['input']['agent_preference']: {agent_type}")
        
        # 3. Verificar si hay un campo reasoning que contenga pistas
        elif "reasoning" in agent_output and "finance" in agent_output["reasoning"].lower():
            agent_type = "finance_agent"
            logger.info(f"Tipo de agente deducido del razonamiento: {agent_type}")
        elif "reasoning" in agent_output and "marketing" in agent_output["reasoning"].lower():
            agent_type = "marketing_agent"
            logger.info(f"Tipo de agente deducido del razonamiento: {agent_type}")
        elif "reasoning" in agent_output and "análisis" in agent_output["reasoning"].lower():
            agent_type = "analysis_agent"
            logger.info(f"Tipo de agente deducido del razonamiento: {agent_type}")
            
        # 4. Si todavía no tenemos agent_type, analizar la query para determinar el agente
        if not agent_type and "query" in state:
            query = state["query"]
            if "financi" in query.lower() or "finanz" in query.lower() or "económic" in query.lower():
                agent_type = "finance_agent"
                logger.info(f"Tipo de agente deducido de la consulta (keywords financieras): {agent_type}")
            elif "market" in query.lower() or "venta" in query.lower() or "client" in query.lower():
                agent_type = "marketing_agent"
                logger.info(f"Tipo de agente deducido de la consulta (keywords marketing): {agent_type}")
            else:
                agent_type = "analysis_agent"  # Valor por defecto
                logger.info(f"Tipo de agente por defecto: {agent_type}")
         
        # Registrar en los logs para depuración
        logger.info(f"Router ha clasificado la consulta como: {agent_type}")
        
        # Mapeo de los tipos de agentes devueltos por router_agent a los nodos del grafo
        if agent_type == "finance_agent":
            return "finance"
        elif agent_type == "marketing_agent":
            return "marketing"
        elif agent_type == "analysis_agent":
            return "analysis"
        else:
            logger.warning(f"Tipo de agente desconocido: {agent_type}")
            return END
    
    def _process_finance(self, state: AgentState) -> AgentState:
        """Procesa la consulta usando el agente de finanzas."""
        query = state["query"]
        context = state["context"]
        
        input_data = {
            "query": query,
            "context": context
        }
        
        try:
            result = self.finance.execute(input_data)
            logger.info(f"Agente de finanzas ha procesado la consulta")
            return {"agent_output": result, "current_agent": "finance", **state}
        except Exception as e:
            logger.error(f"Error en el agente de finanzas: {str(e)}")
            return {"agent_output": {"error": str(e)}, "current_agent": "finance", **state}
    
    def _process_marketing(self, state: AgentState) -> AgentState:
        """Procesa la consulta usando el agente de marketing."""
        query = state["query"]
        context = state["context"]
        
        input_data = {
            "query": query,
            "context": context
        }
        
        try:
            result = self.marketing.execute(input_data)
            logger.info(f"Agente de marketing ha procesado la consulta")
            return {"agent_output": result, "current_agent": "marketing", **state}
        except Exception as e:
            logger.error(f"Error en el agente de marketing: {str(e)}")
            return {"agent_output": {"error": str(e)}, "current_agent": "marketing", **state}
    
    def _process_analysis(self, state: AgentState) -> AgentState:
        """Procesa la consulta usando el agente de análisis."""
        query = state["query"]
        context = state["context"]
        
        input_data = {
            "query": query,
            "context": context
        }
        
        try:
            result = self.analysis.execute(input_data)
            logger.info(f"Agente de análisis ha procesado la consulta")
            return {"agent_output": result, "current_agent": "analysis", **state}
        except Exception as e:
            logger.error(f"Error en el agente de análisis: {str(e)}")
            return {"agent_output": {"error": str(e)}, "current_agent": "analysis", **state}
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta el flujo de agentes sobre los datos de entrada.
        
        Args:
            input_data: Datos de entrada para el flujo de agentes
            
        Returns:
            Resultado final del flujo de agentes
        """
        try:
            # Extraer query y context
            query = input_data.get('query', '')
            context = input_data.get('context', {})
            query_preview = query[:50] + "..." if len(query) > 50 else query
            logger.info(f"Iniciando ejecución del grafo de agentes con input: {query_preview}")
            
            # Imprimir para depuración
            print(f"*** ENTRADA AL GRAFO: {input_data} ***")
            
            # Comprobar si ya tiene la estructura AgentState para no duplicar
            if "agent_output" in input_data and "current_agent" in input_data:
                # Ya tiene estructura AgentState, lo usamos directamente
                state = input_data
                logger.info("Usando el estado proporcionado directamente")
            else:
                # Configurar el estado inicial
                state = {
                    "query": query,
                    "context": context,
                    "agent_output": {},  # Inicializar vacío, el nodo router lo actualizará
                    "current_agent": "router"  # Empezamos siempre con el router
                }
                logger.info("Estado inicial configurado desde cero")
            
            # Imprimir para depuración
            print(f"*** ESTADO INICIAL DEL GRAFO: {state} ***")
            
            # Ejecutar el flujo
            result = self.graph.invoke(state)
            
            # Imprimir para depuración 
            print(f"*** RESULTADO BRUTO DEL GRAFO: {result} ***")
            
            # Detectar si estamos en el caso donde el agente especializado no recibió la información
            if result.get("current_agent") == "router" and not result.get("agent_output"):
                # Intentar recuperar el resultado directamente del agente especializado
                # basándonos en el resultado del router que debería estar en state["agent_output"]
                agent_type = None
                
                # Obtener el tipo de agente desde el router
                router_result = state.get("agent_output", {})
                if isinstance(router_result, dict) and "agent" in router_result:
                    agent_type = router_result["agent"]
                    logger.info(f"Recuperando tipo de agente desde router: {agent_type}")
                
                if agent_type == "finance_agent":
                    # Llamar directamente al agente financiero
                    finance_result = self.finance.execute({"query": query, "context": context})
                    logger.info(f"Llamada directa al agente financiero realizada")
                    return finance_result
                elif agent_type == "marketing_agent":
                    # Llamar directamente al agente de marketing
                    marketing_result = self.marketing.execute({"query": query, "context": context})
                    logger.info(f"Llamada directa al agente de marketing realizada")
                    return marketing_result
                elif agent_type == "analysis_agent":
                    # Llamar directamente al agente de análisis
                    analysis_result = self.analysis.execute({"query": query, "context": context})
                    logger.info(f"Llamada directa al agente de análisis realizada")
                    return analysis_result
            
            # Extraer y devolver la salida final
            final_output = {}
            
            # La respuesta puede venir de diferentes maneras:
            # 1. Del último agente especializado (finance, marketing, analysis)
            if result.get("current_agent") in ["finance", "marketing", "analysis"] and result.get("agent_output"):
                # Tomar la salida del agente especializado
                final_output = result.get("agent_output", {})
                logger.info(f"Usando salida del agente especializado: {result.get('current_agent')}")
            # 2. Del router (si terminó ahí por alguna razón)
            elif result.get("current_agent") == "router" and result.get("agent_output"):
                # Tomar la salida del router
                final_output = result.get("agent_output", {})
                logger.info("Usando salida del router (no se usó agente especializado)")
            # 3. Salida por defecto si no hay nada
            else:
                final_output = {
                    "result": "No se obtuvo respuesta de ningún agente",
                    "agent": "unknown",
                    "confidence": 0.0
                }
                logger.warning("No se encontró una salida válida de ningún agente")
            
            logger.info("Ejecución del grafo de agentes completada con éxito")
            
            # Asegurarse de que haya un campo result siempre
            if "result" not in final_output:
                if "response" in final_output:
                    final_output["result"] = final_output["response"]
                else:
                    final_output["result"] = "Análisis completado con éxito"
            
            return final_output
            
        except Exception as e:
            logger.error(f"Error en ejecución del grafo de agentes: {str(e)}")
            return {
                "error": f"Error en el flujo de agentes: {str(e)}",
                "result": f"Error en el procesamiento: {str(e)}",
                "input": input_data.get("query", ""),
                "agent": "error",
                "confidence": 0.0
            } 
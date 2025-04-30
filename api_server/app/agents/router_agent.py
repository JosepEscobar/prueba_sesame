from typing import Dict, Any, List
import time

from langchain_core.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.core.logging import logger
from app.core.config import get_settings
from langchain_openai import ChatOpenAI

# Obtener la configuración
settings = get_settings()

# Función para crear un LLM que puede ser reemplazado en los tests
def create_llm():
    """Crea y retorna una instancia del modelo de lenguaje."""
    
    # Verificar si hay una clave API configurada
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-your-key-here":
        logger.warning("No se ha configurado una clave API de OpenAI válida.")
        # En este caso, retornar None en lugar de un modelo
        return None
    
    # Si hay una clave API, crear el modelo como de costumbre
    return ChatOpenAI(
        model_name=settings.OPENAI_MODEL,
        temperature=settings.TEMPERATURE,
        streaming=True
    )

# LLM global que puede ser sustituido desde los tests
llm = create_llm()

class RouterAgent(BaseAgent):
    """
    Agente Router que determina qué agente especializado debe manejar una consulta.
    
    El Router analiza la consulta entrante y la dirige al agente más adecuado
    basándose en su contenido, contexto y requerimientos específicos.
    """
    
    def __init__(self, model=None):
        """Inicializa el agente router."""
        super().__init__(
            name="router_agent",
            description="Agente de enrutamiento que dirige consultas a agentes especializados."
        )
        # Asignar el LLM importado a la propiedad de la instancia
        self.llm = llm
        # Definir los agentes disponibles y sus capacidades
        self.available_agents = {
            "analysis_agent": {
                "description": "Especialista en análisis de información compleja.",
                "capabilities": [
                    "análisis de datos",
                    "procesamiento de documentos",
                    "extracción de insights",
                    "identificación de patrones",
                    "resumen de información",
                    "análisis FODA"
                ]
            },
            "action_agent": {
                "description": "Especialista en recomendaciones y acciones concretas.",
                "capabilities": [
                    "planificación estratégica",
                    "recomendaciones tácticas",
                    "planes de implementación",
                    "priorización de acciones",
                    "definición de procesos"
                ]
            },
            "summary_agent": {
                "description": "Especialista en síntesis de información.",
                "capabilities": [
                    "condensación de contenido",
                    "extracción de puntos clave",
                    "síntesis de información",
                    "jerarquización de datos",
                    "resumen ejecutivo"
                ]
            },
            "finance_agent": {
                "description": "Especialista en análisis financiero y consultoría económica.",
                "capabilities": [
                    "análisis financiero",
                    "planificación de presupuestos",
                    "optimización fiscal",
                    "estrategias de inversión",
                    "gestión de riesgos financieros",
                    "valuación empresarial",
                    "análisis de rentabilidad",
                    "modelos financieros",
                    "planificación de flujo de caja"
                ]
            },
            "marketing_agent": {
                "description": "Especialista en estrategias de marketing y análisis de mercado.",
                "capabilities": [
                    "estrategia de marketing",
                    "posicionamiento de marca",
                    "marketing digital",
                    "segmentación de mercado",
                    "análisis competitivo",
                    "estrategia de contenidos",
                    "optimización de canales",
                    "análisis de audiencia",
                    "customer journey",
                    "planificación de campañas"
                ]
            }
        }
        logger.info(f"Agente Router inicializado con {len(self.available_agents)} agentes disponibles")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un agente router que decide qué agente especializado debe manejar una consulta empresarial.
            
            # Agentes disponibles
            
            1. Agente de Análisis (analysis) - Para análisis detallado, identificación de patrones, insights
            2. Agente de Acción (action) - Para recomendaciones prácticas, pasos a seguir, planes
            3. Agente de Resumen (summary) - Para resumir información compleja, extraer puntos clave
            4. Agente de Finanzas (finance) - Para análisis financiero, inversiones, presupuestos
            5. Agente de Marketing (marketing) - Para estrategias de marketing, promoción, publicidad
            
            Analiza la consulta del usuario y elige el agente más apropiado.
            Responde SOLAMENTE con el nombre del agente elegido, sin explicaciones ni formato.
            Usa exactamente uno de: "analysis", "action", "summary", "finance", o "marketing"."""),
            ("human", "{query}")
        ])
    
    def _execute_impl(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta el análisis de la consulta y determina qué agente debe procesarla.
        
        Args:
            input_data: Diccionario con los datos de entrada, que debe incluir 'query' y 
                      opcionalmente 'context' y 'agent_preference'
        
        Returns:
            Diccionario con el agente seleccionado, la consulta original y confianza
        """
        start_time = time.time()
        try:
            # Extraer la consulta y el contexto
            query = input_data.get("query", "")
            context = input_data.get("context", {})
            agent_preference = input_data.get("agent_preference")
            
            # Logueamos solo los primeros 50 caracteres de la consulta como texto, no como slice
            query_preview = query[:50] + "..." if len(query) > 50 else query
            logger.info(f"RouterAgent analizando consulta: {query_preview}")
            
            # Si hay una preferencia de agente, respetarla si el agente existe
            if agent_preference:
                agent_key = f"{agent_preference}"
                if agent_key in self.available_agents:
                    logger.info(f"Usando agente preferido por el usuario: {agent_key}")
                    return {
                        "agent": agent_key,
                        "input": input_data,
                        "confidence": 1.0,
                        "reasoning": "Seleccionado por preferencia explícita del usuario"
                    }
                else:
                    logger.warning(f"Agente preferido '{agent_key}' no encontrado, realizando selección automática")
            
            # Si no hay un LLM configurado (por falta de API key), devolver un error
            if self.llm is None:
                logger.error("Error: No hay clave API de OpenAI válida. Imposible enrutar la consulta.")
                return {
                    "error": "No se ha configurado una clave API de OpenAI válida. Para utilizar este agente, configure la clave en el archivo .env",
                    "agent": "error",
                    "input": input_data,
                    "confidence": 0.0,
                    "success": False
                }
            
            # Preparar el prompt con la consulta y contexto
            prompt_input = self._prepare_router_prompt(query, context)
            
            # Invocar el LLM para obtener una decisión
            response = self.llm.invoke(prompt_input)
            response_content = response.content.strip().lower()
            
            # Mapear la respuesta simple al nombre del agente
            agent_mapping = {
                "analysis": "analysis_agent",
                "action": "action_agent", 
                "summary": "summary_agent",
                "finance": "finance_agent",
                "marketing": "marketing_agent"
            }
            
            agent = agent_mapping.get(response_content, "analysis_agent")
            
            logger.info(f"RouterAgent seleccionó {agent} con confianza 0.6")
            
            # Crear la decisión
            decision = {
                "agent": agent,
                "input": input_data,
                "confidence": 0.6,
                "reasoning": "Seleccionado por análisis de la consulta"
            }
            
            # Decidir si se necesita un resumen después del procesamiento
            if len(query) > 500 or context.get("summarize_result", False):
                decision["needs_summary"] = True
                
            return decision
            
        except Exception as e:
            logger.error(f"Error en RouterAgent: {str(e)}")
            return {
                "error": f"Error en enrutamiento: {str(e)}",
                "agent": "error",
                "input": input_data,
                "confidence": 0.0
            }
    
    def _prepare_router_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """
        Prepara el prompt para el router.
        
        Args:
            query: La consulta del usuario
            context: Contexto adicional para la consulta
            
        Returns:
            Prompt formateado para el LLM
        """
        # Incluir información de contexto si está disponible
        context_text = ""
        if context:
            context_text = "\n\nContexto adicional:\n"
            for key, value in context.items():
                context_text += f"- {key}: {value}\n"
        
        # Combinar consulta y contexto
        full_query = f"{query}{context_text}"
        
        # Formatear el prompt usando el formato definido en el ChatPromptTemplate
        formatted_prompt = self.prompt.format(query=full_query)
        
        return formatted_prompt 
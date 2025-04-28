from typing import Dict, Any, List
import time

from langchain_core.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.core.logging import logger
from app.core.config import settings
import re
import json

class RouterAgent(BaseAgent):
    """
    Agente Router que determina qué agente especializado debe manejar una consulta.
    
    El Router analiza la consulta entrante y la dirige al agente más adecuado
    basándose en su contenido, contexto y requerimientos específicos.
    """
    
    def __init__(self):
        """Inicializa el agente router."""
        super().__init__(
            name="router_agent",
            description="Agente de enrutamiento que dirige consultas a agentes especializados."
        )
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
            ("system", """Eres un agente router inteligente que decide qué agente especializado debe manejar una consulta empresarial.
            
            # Agentes disponibles y sus capacidades
            
            1. Agente de Marketing (marketing):
               - Especializado en estrategias de marketing y promoción
               - Proporciona recomendaciones sobre marketing digital, SEO, redes sociales, branding
               - Ideal para: consultas sobre campañas, estrategias de mercado, posicionamiento de marca
            
            2. Agente de Finanzas (finance):
               - Especializado en análisis financiero y gestión económica
               - Proporciona análisis de costos, proyecciones financieras, valoraciones
               - Ideal para: consultas sobre inversiones, presupuestos, valoración de empresas, ROI
            
            3. Agente de Operaciones (operations):
               - Especializado en procesos operativos y logística
               - Proporciona optimización de procesos, gestión de cadena de suministro
               - Ideal para: consultas sobre eficiencia operativa, procesos, logística
            
            4. Agente de Búsqueda de Datos (data_lookup):
               - Especializado en buscar información externa
               - Consulta bases de datos, artículos y fuentes externas
               - Ideal para: cuando se requieren datos específicos o actualizados
               - NOTA: Este agente debe ser usado SOLO cuando la consulta requiere información muy específica o actualizada que no tendrían los otros agentes
            
            # Tu tarea
            
            1. Analiza cuidadosamente la consulta del usuario
            2. Determina qué agente es el más apropiado basándote en:
               - El tema principal de la consulta
               - El tipo de respuesta que necesita el usuario
               - La especialización requerida
            3. Calcula un nivel de confianza (0.0 a 1.0) para tu decisión
            
            # Formato de respuesta
            
            Responde en formato JSON con la siguiente estructura exacta:
            ```json
            {
                "agent": "nombre_del_agente",
                "reasoning": "explicación breve de tu razonamiento",
                "confidence": 0.X
            }
            ```
            
            Donde "nombre_del_agente" debe ser exactamente uno de: "marketing", "finance", "operations", o "data_lookup".
            No incluyas comentarios adicionales, solo el objeto JSON.
            """),
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
            
            logger.info(f"RouterAgent analizando consulta: {query[:50]}...")
            
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
            
            # Preparar el prompt con la consulta y contexto
            prompt_input = self._prepare_router_prompt(query, context)
            
            # Invocar el LLM para obtener una decisión
            response = self.llm.invoke(prompt_input)
            response_content = response.content
            
            # Extraer la decisión del agente
            decision = self._extract_agent_decision(response_content)
            
            # Verificar si el agente existe
            agent = decision.get("agent", "")
            if not agent.endswith("_agent"):
                agent = f"{agent}_agent"
                decision["agent"] = agent
                
            logger.info(f"RouterAgent seleccionó {agent} con confianza {decision.get('confidence', 0)}")
            
            # Incluir el input original para que el agente tenga acceso a los datos completos
            decision["input"] = input_data
            
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
        
        return full_query
    
    def _extract_agent_from_response(self, response: str) -> str:
        """
        Extrae el nombre del agente de la respuesta del LLM.
        
        Args:
            response: Respuesta en texto del LLM
            
        Returns:
            Nombre del agente seleccionado
        """
        # Intentar extraer JSON de la respuesta
        try:
            # Intentar encontrar un objeto JSON en la respuesta
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                decision = json.loads(json_str)
                return decision.get("agent", "analysis_agent")
        except:
            pass
        
        # Fallback - buscar menciones de agentes en el texto
        agent_mapping = {
            "marketing": "marketing_agent",
            "finanzas": "finance_agent", 
            "financiero": "finance_agent",
            "análisis": "analysis_agent",
            "acción": "action_agent",
            "resumen": "summary_agent"
        }
        
        for keyword, agent in agent_mapping.items():
            if keyword.lower() in response.lower():
                return agent
                
        # Por defecto, usar el agente de análisis
        return "analysis_agent"
    
    def _extract_agent_decision(self, response_content: str) -> Dict[str, Any]:
        """
        Extrae la decisión completa (agente, razonamiento, confianza) de la respuesta.
        
        Args:
            response_content: Respuesta en texto del LLM
            
        Returns:
            Diccionario con la decisión extraída
        """
        try:
            # Intentar encontrar un objeto JSON en la respuesta
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                decision = json.loads(json_str)
                
                # Validar y normalizar la decisión
                agent = decision.get("agent", "")
                if agent:
                    # Convertir nombres simplificados a formato completo
                    agent_mapping = {
                        "marketing": "marketing_agent",
                        "finance": "finance_agent",
                        "analysis": "analysis_agent",
                        "action": "action_agent",
                        "summary": "summary_agent",
                        "data_lookup": "data_lookup_agent"
                    }
                    
                    if agent in agent_mapping:
                        decision["agent"] = agent_mapping[agent]
                    
                # Asegurar que hay un valor de confianza
                if "confidence" not in decision:
                    decision["confidence"] = 0.8
                    
                return decision
                
        except Exception as e:
            logger.error(f"Error al extraer decisión JSON: {str(e)}")
            
        # Fallback - crear una decisión básica
        default_agent = self._extract_agent_from_response(response_content)
        return {
            "agent": default_agent,
            "reasoning": "Extraído por análisis de texto (fallback)",
            "confidence": 0.6
        } 
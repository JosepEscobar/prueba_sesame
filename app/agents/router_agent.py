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
                "description": "Analiza información compleja y proporciona resúmenes detallados.",
                "capabilities": [
                    "análisis de datos", 
                    "extracción de insights", 
                    "procesamiento de documentos", 
                    "resumen de información",
                    "identificación de patrones",
                    "análisis FODA"
                ]
            },
            "action_agent": {
                "description": "Ejecuta acciones concretas y tareas operativas.",
                "capabilities": [
                    "automatización de tareas", 
                    "ejecución de procesos", 
                    "seguimiento de procedimientos", 
                    "implementación de soluciones",
                    "gestión de flujos de trabajo",
                    "optimización de operaciones"
                ]
            },
            "summary_agent": {
                "description": "Genera resúmenes concisos y puntos clave de información extensa.",
                "capabilities": [
                    "condensación de contenido", 
                    "extracción de puntos clave", 
                    "síntesis de información", 
                    "jerarquización de datos",
                    "resumen ejecutivo",
                    "priorización de información"
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
            ("human", """Consulta del usuario:
            
            {query}
            
            Contenido adicional (si está disponible):
            {content}
            
            Solicitud de acción (si está disponible):
            {action_request}
            """)
        ])
        
    def _execute_impl(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementa la lógica para determinar qué agente debe manejar la consulta.
        
        Args:
            input_data: Datos de entrada que contienen la consulta y contexto
            
        Returns:
            Diccionario con el agente seleccionado, input original y nivel de confianza
        """
        start_time = time.time()
        query = input_data.get("query", "")
        logger.info(f"Router procesando consulta: {query[:100]}...")
        
        # Preparar input para el prompt
        prompt = self._prepare_router_prompt(query, input_data)
        
        # Invocar el modelo para decidir el agente más adecuado
        response = self.llm.invoke(prompt)
        
        # Procesar la respuesta para extraer el agente seleccionado
        selected_agent = self._extract_agent_from_response(response.content)
        
        # Verificar que el agente existe
        if selected_agent not in self.available_agents:
            logger.warning(f"Agente seleccionado '{selected_agent}' no válido, usando default 'analysis_agent'")
            selected_agent = "analysis_agent"
            confidence = 0.5
        else:
            confidence = 0.8  # Confianza predeterminada para decisiones de enrutamiento
            logger.info(f"Consulta enrutada a: {selected_agent} (confianza: {confidence})")
        
        processing_time = time.time() - start_time
        logger.info(f"Decisión de enrutamiento tomada en {processing_time:.2f} segundos")
        
        return {
            "agent": selected_agent,
            "input": input_data,
            "confidence": confidence
        }
    
    def _prepare_router_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """
        Prepara el prompt para el modelo de enrutamiento.
        
        Args:
            query: La consulta del usuario
            context: Contexto adicional
            
        Returns:
            Prompt formateado
        """
        # Construir la descripción de los agentes para el prompt
        agents_description = ""
        for agent_name, details in self.available_agents.items():
            capabilities = ", ".join(details["capabilities"])
            agents_description += f"* {agent_name}: {details['description']}\n  Capacidades: {capabilities}\n\n"
        
        prompt = f"""
        Como sistema de enrutamiento, tu tarea es determinar qué agente especializado 
        debe manejar la siguiente consulta. Analiza cuidadosamente la naturaleza de 
        la solicitud y selecciona el agente más adecuado.
        
        ## Consulta a clasificar:
        {query}
        
        ## Contexto adicional:
        {context}
        
        ## Agentes disponibles:
        {agents_description}
        
        ## Instrucciones:
        1. Analiza la consulta y determina su naturaleza principal
        2. Identifica los requerimientos específicos y el área de especialización necesaria
        3. Selecciona UN SOLO agente entre las opciones disponibles que mejor se adapte
        4. Proporciona una breve explicación de por qué ese agente es el más adecuado
        
        ## Formato de respuesta:
        Responde SOLAMENTE con el nombre del agente seleccionado seguido de una breve justificación, en este formato exacto:
        AGENTE: [nombre_del_agente]
        JUSTIFICACIÓN: [breve explicación de 1-2 oraciones]
        """
        
        return prompt
    
    def _extract_agent_from_response(self, response: str) -> str:
        """
        Extrae el nombre del agente seleccionado desde la respuesta del modelo.
        
        Args:
            response: Respuesta del modelo LLM
            
        Returns:
            Nombre del agente seleccionado
        """
        try:
            # Buscar el formato "AGENTE: [nombre_del_agente]" en la respuesta
            for line in response.split('\n'):
                if line.strip().startswith('AGENTE:'):
                    agent_name = line.split(':', 1)[1].strip().lower()
                    # Eliminar cualquier carácter no alfanumérico y convertir a snake_case
                    agent_name = ''.join(c if c.isalnum() or c == '_' else '' for c in agent_name)
                    if not agent_name.endswith('_agent'):
                        agent_name += '_agent'
                    return agent_name
            
            # Si no se encontró el formato esperado, usar análisis heurístico
            response_lower = response.lower()
            for agent_name in self.available_agents.keys():
                agent_base = agent_name.replace('_agent', '')
                if agent_base in response_lower or agent_name in response_lower:
                    return agent_name
            
            # Default fallback
            logger.warning(f"No se pudo extraer un agente válido de la respuesta: {response[:100]}...")
            return "analysis_agent"
        
        except Exception as e:
            logger.error(f"Error al extraer agente de respuesta: {str(e)}")
            return "analysis_agent"
    
    def _extract_agent_decision(self, response_content: str) -> Dict[str, Any]:
        """Extrae la decisión del agente desde la respuesta en formato JSON."""
        # Intentar extraer el JSON
        try:
            # Buscar contenido JSON entre llaves
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                agent_info = json.loads(json_match.group(0))
                
                # Validar campos requeridos
                if "agent" not in agent_info or "confidence" not in agent_info:
                    raise ValueError("Faltan campos requeridos en la respuesta")
                
                # Asegurar que el agente es uno de los válidos
                valid_agents = ["marketing", "finance", "operations", "data_lookup", "analysis", "action", "summary"]
                if agent_info["agent"].lower() not in valid_agents:
                    raise ValueError(f"Agente no válido: {agent_info['agent']}")
                
                # Estandarizar la respuesta
                return {
                    "agent": agent_info["agent"].lower(),
                    "reasoning": agent_info.get("reasoning", "No se proporcionó razonamiento"),
                    "confidence": float(agent_info["confidence"])
                }
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Error al extraer decisión del agente: {str(e)}")
            logger.error(f"Contenido de la respuesta: {response_content}")
        
        # Si hay algún error, devolver una respuesta por defecto
        return {
            "agent": "marketing",  # Agente por defecto
            "reasoning": "Decisión por defecto debido a error en procesamiento",
            "confidence": 0.5
        } 
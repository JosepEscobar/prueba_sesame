from typing import Dict, Any, Tuple
from langchain.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.core.logging import logger
import re

class RouterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Router Agent",
            description="Agente que decide qué agente especializado debe manejar la solicitud"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un agente router inteligente que decide qué agente especializado debe manejar una solicitud.
            
            # Agentes disponibles y sus capacidades
            
            1. Agente de Análisis:
               - Realiza análisis detallado de datos, textos, y patrones
               - Extrae insights y conclusiones relevantes
               - Ideal para: análisis de sentimiento, análisis de tendencias, análisis de datos, comprensión de textos complejos
            
            2. Agente de Acción:
               - Ejecuta acciones específicas y concretas
               - Proporciona planes paso a paso para tareas
               - Ideal para: realizar tareas, ejecutar comandos, tomar decisiones operativas
            
            3. Agente de Resumen:
               - Condensa información extensa en puntos clave
               - Crea resúmenes concisos manteniendo el contexto esencial
               - Ideal para: resumir documentos, crear síntesis de información, extraer puntos principales
            
            # Tu tarea
            
            1. Analiza cuidadosamente la solicitud del usuario
            2. Determina qué agente es el más apropiado basándote en:
               - La naturaleza de la solicitud
               - Las palabras clave utilizadas
               - El resultado esperado por el usuario
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
            
            Donde "nombre_del_agente" debe ser exactamente uno de: "analysis", "action", o "summary".
            No incluyas comentarios adicionales, solo el objeto JSON.
            """),
            ("human", """Solicitud del usuario:
            
            {query}
            
            Contenido adicional (si está disponible):
            {content}
            
            Solicitud de acción (si está disponible):
            {action_request}
            """)
        ])
        
    async def _execute_impl(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el proceso de enrutamiento."""
        # Preparar el input para el prompt
        prompt_input = {
            "query": input_data.get("query", ""),
            "content": input_data.get("content", "No hay contenido adicional"),
            "action_request": input_data.get("action_request", "No hay solicitud de acción")
        }
        
        logger.info(
            f"RouterAgent procesando solicitud",
            extra={
                "agent_name": self.name,
                "input_query": prompt_input["query"][:100] + "..." if len(prompt_input["query"]) > 100 else prompt_input["query"]
            }
        )
        
        # Obtener la respuesta del LLM
        chain = self.prompt | self.llm
        response = await chain.ainvoke(prompt_input)
        
        # Extraer la decisión y confianza del JSON
        agent_info = self._extract_agent_decision(response.content)
        
        logger.info(
            f"RouterAgent decidió usar {agent_info['agent']}",
            extra={
                "agent_name": self.name,
                "decision": agent_info["agent"],
                "confidence": agent_info["confidence"],
                "reasoning": agent_info["reasoning"]
            }
        )
        
        return {
            "agent_decision": agent_info["agent"],
            "reasoning": agent_info["reasoning"],
            "original_input": input_data,
            "confidence": agent_info["confidence"]
        }
    
    def _extract_agent_decision(self, response_content: str) -> Dict[str, Any]:
        """Extrae la decisión del agente desde la respuesta en formato JSON."""
        # Intentar extraer el JSON
        try:
            # Buscar contenido JSON entre llaves
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                import json
                agent_info = json.loads(json_match.group(0))
                
                # Validar campos requeridos
                if "agent" not in agent_info or "confidence" not in agent_info:
                    raise ValueError("Faltan campos requeridos en la respuesta")
                
                # Asegurar que el agente es uno de los válidos
                valid_agents = ["analysis", "action", "summary"]
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
            "agent": "analysis",  # Agente por defecto
            "reasoning": "Decisión por defecto debido a error en procesamiento",
            "confidence": 0.5
        } 
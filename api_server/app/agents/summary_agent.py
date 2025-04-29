"""
Agent encargado de crear resúmenes concisos y claros de información compleja.
"""

from typing import Dict, Any, List, Optional
import time
import json

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.core.logging import logger
from app.core.config import get_settings

# Obtener la configuración
settings = get_settings()

# Función para crear un LLM que puede ser reemplazado en los tests
def create_llm():
    return ChatOpenAI(
        model_name=settings.OPENAI_MODEL,
        temperature=settings.TEMPERATURE,
        api_key=settings.OPENAI_API_KEY,
    )

# LLM global que puede ser sustituido desde los tests
llm = create_llm()

class SummaryAgent(BaseAgent):
    """
    Agente especializado en generar resúmenes claros, concisos y estructurados de
    información compleja. Este agente es útil para condensar análisis extensos,
    reportes de mercado o grandes volúmenes de información en puntos clave.
    """
    
    def __init__(self, model=None):
        """Inicializa el SummaryAgent"""
        super().__init__(
            name="summary_agent",
            description="Especialista en síntesis de información."
        )
        # Asignar el LLM importado a la propiedad de la instancia
        self.llm = llm
        logger.info(f"SummaryAgent inicializado")
    
    def _execute_impl(self, input_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Ejecuta la operación de resumen basada en los datos de entrada.
        
        Args:
            input_data: Diccionario que contiene la consulta y cualquier contexto adicional.
                Debe incluir 'query' y opcionalmente 'context'.
                
        Returns:
            Dict con los resultados del resumen, la consulta original y un nivel de confianza.
        """
        try:
            logger.info(f"SummaryAgent procesando solicitud: {input_data.get('query', '')[:50]}...")
            
            # Extraer la consulta y el contexto
            query = input_data.get("query", "")
            context = input_data.get("context", "")
            
            # Preparar el prompt para el resumen
            prompt = f"""
            Eres un experto en crear resúmenes claros, concisos y estructurados. Tu tarea es generar un resumen
            de la siguiente información:
            
            CONSULTA: {query}
            
            CONTEXTO ADICIONAL: {context}
            
            Instrucciones para el resumen:
            1. Identifica los puntos clave y las ideas principales.
            2. Elimina información redundante o detalles excesivos.
            3. Organiza la información en una estructura lógica y coherente.
            4. Utiliza un lenguaje claro, preciso y profesional.
            5. Adapta el nivel de detalle según la complejidad del contenido.
            6. Incluye conclusiones importantes si las hay.
            
            Tu resumen debe ser completo pero conciso, presentando las ideas principales de forma estructurada.
            """
            
            # Invocar el LLM para obtener un resumen
            start_time = time.time()
            response = self.llm.invoke(prompt)
            processing_time = time.time() - start_time
            
            logger.info(f"SummaryAgent completó la generación del resumen en {processing_time:.2f} segundos")
            
            return {
                "summary_result": response.content,
                "result": response.content,  # Para compatibilidad con la prueba
                "input": input_data,
                "confidence": 0.85,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error en SummaryAgent: {str(e)}")
            return {
                "error": str(e),
                "input": input_data,
                "confidence": 0.0,
                "processing_time": 0.0
            } 
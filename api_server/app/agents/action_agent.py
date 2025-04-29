from typing import Dict, Any
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
    return ChatOpenAI(
        model_name=settings.OPENAI_MODEL,
        temperature=settings.TEMPERATURE,
        api_key=settings.OPENAI_API_KEY,
    )

# LLM global que puede ser sustituido desde los tests
llm = create_llm()

class ActionAgent(BaseAgent):
    def __init__(self, model=None):
        super().__init__(
            name="action_agent",
            description="Agente especializado en realizar acciones específicas"
        )
        # Asignar el LLM importado a la propiedad de la instancia
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un agente especializado en realizar acciones específicas.
            Tu objetivo es ejecutar tareas concretas y proporcionar resultados tangibles.
            
            Debes:
            1. Identificar la acción requerida
            2. Planificar los pasos necesarios
            3. Ejecutar la acción de manera eficiente
            4. Proporcionar un reporte detallado del resultado
            
            Formatea tu respuesta incluyendo:
            - Acción realizada
            - Pasos ejecutados
            - Resultado obtenido
            - Recomendaciones posteriores"""),
            ("human", "{input}")
        ])
        
    def _execute_impl(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la acción solicitada."""
        start_time = time.time()
        
        # Extraer la consulta
        query = input_data.get("query", "")
        
        # Formatear el prompt correctamente
        formatted_prompt = self.prompt.format(input=query)
        
        # Obtener la respuesta del LLM
        response = self.llm.invoke(formatted_prompt)
        
        processing_time = time.time() - start_time
        logger.info(f"ActionAgent completó la acción en {processing_time:.2f} segundos")
        
        return {
            "action_result": response.content,
            "input": input_data,
            "confidence": 0.85,
            "processing_time": processing_time
        } 
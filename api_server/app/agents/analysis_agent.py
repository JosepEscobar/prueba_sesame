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
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-key-here":
        return ChatOpenAI(
            model_name=settings.OPENAI_MODEL,
            temperature=settings.TEMPERATURE,
            api_key=settings.OPENAI_API_KEY,
        )
    logger.warning("No hay clave API de OpenAI válida configurada.")
    return None

# LLM global que puede ser sustituido desde los tests
llm = create_llm()

class AnalysisAgent(BaseAgent):
    def __init__(self, model=None):
        super().__init__(
            name="analysis_agent",
            description="Agente especializado en análisis detallado de datos y textos"
        )
        # Asignar el LLM importado a la propiedad de la instancia
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un agente especializado en análisis detallado de datos y textos.
            Tu objetivo es proporcionar análisis profundos, identificar patrones, y extraer insights valiosos.
            
            Debes:
            1. Analizar el contenido en detalle
            2. Identificar patrones y tendencias
            3. Extraer conclusiones relevantes
            4. Proporcionar recomendaciones basadas en el análisis
            
            Formatea tu respuesta de manera clara y estructurada."""),
            ("human", "{input}")
        ])
        
    def _execute_impl(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el análisis del contenido proporcionado."""
        start_time = time.time()
        
        # Extraer la consulta
        query = input_data.get("query", "")
        
        # Si no hay un LLM configurado (por falta de API key), devolver un error
        if self.llm is None:
            logger.error("Error: No hay clave API de OpenAI válida. Imposible generar respuesta de análisis.")
            processing_time = time.time() - start_time
            return {
                "result": "",
                "input": input_data,
                "confidence": 0.0,
                "processing_time": processing_time,
                "success": False,
                "error": "No se ha configurado una clave API de OpenAI válida. Para utilizar este agente, configure la clave en el archivo .env"
            }
        
        # Formatear el prompt correctamente
        formatted_prompt = self.prompt.format(input=query)
        
        # Obtener la respuesta del LLM
        response = self.llm.invoke(formatted_prompt)
        
        processing_time = time.time() - start_time
        logger.info(f"AnalysisAgent completó el análisis en {processing_time:.2f} segundos")
        
        return {
            "result": response.content,
            "input": input_data,
            "confidence": 0.9,
            "processing_time": processing_time
        } 
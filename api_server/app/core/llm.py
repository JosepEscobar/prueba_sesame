"""
Módulo para interactuar con modelos de lenguaje (LLM).

Este módulo proporciona funciones y clases para interactuar con diferentes
modelos de lenguaje, incluyendo OpenAI, y gestionar respuestas.
"""

import time
import traceback

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

class LLMClient:
    """
    Cliente para interactuar con modelos de lenguaje.

    Proporciona métodos para generar texto y analizar información usando
    diferentes proveedores de modelos de lenguaje.
    """

    def __init__(self):
        """Inicializa el cliente LLM."""
        self.settings = get_settings()
        self.init_openai_client()

    def init_openai_client(self):
        """Inicializa el cliente de OpenAI."""
        try:
            import openai

            # Configurar API key
            api_key = self.settings.OPENAI_API_KEY
            if not api_key:
                logger.warning("No se encontró API key de OpenAI en la configuración")
                self.openai_client = None
                return

            self.openai_client = openai.OpenAI(api_key=api_key)
            self.model = self.settings.OPENAI_MODEL
            self.temperature = self.settings.TEMPERATURE

            logger.info(f"Cliente OpenAI inicializado con modelo {self.model}")

        except ImportError:
            logger.warning("No se pudo importar la biblioteca OpenAI")
            self.openai_client = None
        except Exception as e:
            logger.error(f"Error al inicializar cliente OpenAI: {str(e)}")
            logger.error(traceback.format_exc())
            self.openai_client = None

    def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Genera texto utilizando el modelo configurado.

        Args:
            prompt: El texto para generar la respuesta
            max_tokens: Número máximo de tokens a generar

        Returns:
            Texto generado
        """
        if not self.openai_client:
            # Fallback para pruebas o cuando no hay API key
            logger.warning("Usando respuesta simulada para LLM (sin API key)")
            return self._simulate_response(prompt)

        try:
            start_time = time.time()

            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un asistente analítico experto en evaluar consultas empresariales."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=max_tokens
            )

            execution_time = time.time() - start_time
            logger.info(f"Respuesta generada por OpenAI en {execution_time:.2f}s (modelo: {self.model})")

            if hasattr(response, 'choices') and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                logger.error("Formato de respuesta inesperado de OpenAI")
                return ""

        except Exception as e:
            logger.error(f"Error al generar texto con OpenAI: {str(e)}")
            logger.error(traceback.format_exc())
            # Usar respuesta simulada como fallback
            return {
                "in_scope": "",
                "domain": "",
                "confidence": 0,
                "reasoning": "Error al generar texto con OpenAI",
                "explanation": "Este es un mensaje de error simulado para pruebas sin API key de OpenAI."
            }

# Cliente LLM singleton
_llm_client = None

def get_llm_client() -> LLMClient:
    """
    Obtiene la instancia del cliente LLM.

    Returns:
        Cliente LLM
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

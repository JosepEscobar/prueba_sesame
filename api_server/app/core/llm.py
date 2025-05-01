"""
Módulo para interactuar con modelos de lenguaje (LLM).

Este módulo proporciona funciones y clases para interactuar con diferentes
modelos de lenguaje, incluyendo OpenAI, y gestionar respuestas.
"""

import json
import time
import traceback
from typing import Any, Dict, TypeVar

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

T = TypeVar("T", bound=Dict[str, Any])


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
                    {
                        "role": "system",
                        "content": "Eres un asistente analítico experto en evaluar consultas empresariales.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=max_tokens,
            )

            execution_time = time.time() - start_time
            logger.info(f"Respuesta generada por OpenAI en {execution_time:.2f}s (modelo: {self.model})")

            if hasattr(response, "choices") and len(response.choices) > 0:
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
                "explanation": "Este es un mensaje de error simulado para pruebas sin API key de OpenAI.",
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


def parse_llm_json_response(
    response: Any, default_value: Dict[str, Any], response_field: str = "content"
) -> Dict[str, Any]:
    """
    Parsea de manera segura una respuesta JSON de un LLM.

    Args:
        response: La respuesta del LLM
        default_value: Valor por defecto a devolver en caso de error
        response_field: Nombre del campo que contiene el texto JSON (por defecto "content")

    Returns:
        Diccionario con el JSON parseado o el valor por defecto en caso de error
    """
    try:
        # Verificar que la respuesta contenga el campo esperado
        if hasattr(response, response_field):
            content = getattr(response, response_field)
            if content and isinstance(content, str) and content.strip():
                # Limpiar el contenido de delimitadores de código markdown
                cleaned_content = content.strip()

                # Eliminar delimitadores de código markdown si existen
                if cleaned_content.startswith("```"):
                    # Encontrar el primer salto de línea después del inicio del bloque de código
                    first_newline = cleaned_content.find("\n")
                    if first_newline != -1:
                        # Eliminar la primera línea (```json)
                        cleaned_content = cleaned_content[first_newline + 1 :]

                # Eliminar el delimitador de cierre si existe
                if cleaned_content.endswith("```"):
                    cleaned_content = cleaned_content.rsplit("```", 1)[0].strip()

                try:
                    # Intenta parsear el JSON limpio
                    result = json.loads(cleaned_content.strip())
                    logger.info("JSON parseado correctamente de la respuesta LLM")
                    return result
                except json.JSONDecodeError as json_err:
                    # Error al parsear JSON
                    logger.error(f"Error al decodificar JSON de respuesta LLM: {json_err}")
                    # Intentar extraer JSON si está envuelto en un formato no estándar
                    try:
                        # Buscar patrones de JSON entre llaves
                        import re

                        json_pattern = r"\{[\s\S]*\}"
                        matches = re.search(json_pattern, cleaned_content)
                        if matches:
                            potential_json = matches.group(0)
                            result = json.loads(potential_json)
                            logger.info("JSON extraído y parseado correctamente después de limpieza adicional")
                            return result
                    except Exception:
                        # Si la extracción adicional falla, usar el valor por defecto
                        pass
                    return default_value

        # Si la respuesta está vacía o no tiene el campo esperado
        logger.error(f"Respuesta del LLM vacía o inválida: {response}")
        return default_value

    except Exception as e:
        logger.error(f"Error inesperado al procesar respuesta LLM: {str(e)}")
        return default_value

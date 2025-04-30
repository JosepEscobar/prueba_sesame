"""
Agent encargado de crear resúmenes concisos y claros de información compleja.
"""

from typing import Dict, Any, List, Optional
import time
import json
import os
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.core.logging import logger
from app.core.config import get_settings
from app.tools.mcp_client import MCPClient

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
        # Inicializar cliente MCP
        mcp_path = str(Path(os.path.abspath(__file__)).parents[3] / "mcp_server" / "main.py")
        self.mcp_client = MCPClient(
            base_url=get_settings().MCP_CLIENT_URL,
            use_stdio=True,
            mcp_server_path=mcp_path
        )
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
            start_time = time.time()
            
            # Extraer la consulta
            query = input_data.get("query", "")
            
            # Loguear la consulta con un límite seguro
            query_preview = query[:50] + "..." if len(query) > 50 else query
            logger.info(f"SummaryAgent procesando solicitud: {query_preview}")
            
            # Extraer el contexto
            context = input_data.get("context", {})
            
            # Convertir contexto a formato de texto
            if isinstance(context, dict):
                # Caso 1: El contexto tiene un campo 'content' directo (caso más común)
                if "content" in context:
                    context_text = context["content"]
                # Caso 2: El contexto tiene una estructura result con content
                elif "result" in context and isinstance(context["result"], dict) and "content" in context["result"]:
                    context_text = context["result"]["content"]
                # Caso 3: El contexto tiene una respuesta directa en result (string)
                elif "result" in context and isinstance(context["result"], str):
                    context_text = context["result"]
                # Caso 4: Hay raw_response disponible (desde el grafo)
                elif "raw_response" in context and context["raw_response"]:
                    # Manejar caso donde raw_response es un objeto AIMessage
                    raw_response = context["raw_response"]
                    if hasattr(raw_response, 'content'):  # Es un objeto tipo AIMessage
                        context_text = raw_response.content
                    else:
                        context_text = str(raw_response)
                # Caso genérico: convertir a JSON para incluirlo completo
                else:
                    context_text = json.dumps(context, indent=2, ensure_ascii=False)
            elif isinstance(context, str):
                context_text = context
            elif hasattr(context, 'content'):  # Manejo directo de AIMessage u objetos similares
                context_text = context.content
            else:
                context_text = str(context)
            
            # Registrar el contenido recibido para ayudar en depuración
            try:
                content_length = len(context_text) if context_text is not None else 0
                logger.info(f"SummaryAgent recibió contenido para resumir de longitud: {content_length}")
                if content_length < 500:  # Solo loguear contenido pequeño completo
                    logger.info(f"Contenido recibido: {context_text}")
                else:
                    logger.info(f"Extracto del contenido: {context_text[:200]}...")
            except Exception as e:
                logger.warning(f"No se pudo determinar longitud del contenido: {str(e)}. Usando método alternativo.")
                # Usar un método alternativo para determinar la longitud
                try:
                    context_text = str(context_text)
                    logger.info(f"Contenido convertido a string, longitud: {len(context_text)}")
                except:
                    logger.error("No se pudo convertir el contenido a string.")
                    context_text = "Error al procesar el contenido."
            
            # Si hay poco o ningún contexto, intentar recopilar información adicional
            if not context_text or context_text.strip() in ["", "{}", "[]"]:
                logger.info("Contexto insuficiente, buscando información...")
                
                try:
                    # Intentar obtener artículos relacionados mediante el cliente MCP
                    articles_data = self.mcp_client.call_tool_sync(
                        "search_articles", 
                        {"query": query}
                    )
                    
                    if articles_data and "result" in articles_data:
                        articles = articles_data["result"]
                        if articles and len(articles) > 0:
                            context_text += "\n\nFuentes de información relevantes encontradas:\n"
                            for i, article in enumerate(articles[:3], 1):
                                context_text += f"{i}. {article.get('title', 'Sin título')}\n"
                                context_text += f"   {article.get('snippet', 'Sin descripción')}\n"
                except Exception as e:
                    logger.warning(f"Error al buscar artículos: {str(e)}")
            
            # Preparar el prompt para el resumen
            prompt = f"""
            Eres un experto en crear resúmenes claros, concisos y estructurados. Tu tarea es generar un resumen
            completo de la siguiente información, preservando todos los detalles importantes.
            
            CONSULTA ORIGINAL: {query}
            
            RESULTADO COMPLETO DEL ANÁLISIS:
            {context_text}
            
            Instrucciones para el resumen:
            1. Mantén todas las ideas principales y conclusiones clave.
            2. Organiza la información en una estructura lógica con secciones claras.
            3. Incluye todas las cifras, métricas y datos específicos importantes.
            4. Preserva recomendaciones y pasos a seguir.
            5. Usa lenguaje claro y profesional.
            6. Debes mantener todo el valor informativo del texto original.
            7. El resumen debe ser tan completo que pueda sustituir al original.
            
            Tu respuesta debe estar bien estructurada, con títulos de sección, párrafos coherentes
            y formato que facilite la lectura y comprensión.
            """
            
            # Si no hay LLM, usar una respuesta básica
            if not self.llm:
                processing_time = time.time() - start_time
                logger.warning("No se pudo generar un resumen detallado (LLM no disponible).")
                return {
                    "result": {
                        "content": "No se pudo generar un resumen detallado. Por favor, revise el resultado completo.",
                        "source": "summary_agent",
                        "success": False
                    },
                    "input": input_data,
                    "confidence": 0.5,
                    "processing_time": processing_time
                }
                
            # Generar el resumen usando el LLM
            from langchain_core.messages import SystemMessage, HumanMessage
            
            messages = [
                SystemMessage(content="Eres un especialista en generar resúmenes concisos, claros y completos."),
                HumanMessage(content=prompt)
            ]
            
            response = self.invoke_llm(messages, prompt_type="langchain")
            summary_content = response.content
            
            # Verificar que el resumen no sea demasiado breve (lo que podría indicar un problema)
            if len(summary_content) < 100 and len(context_text) > 500:
                logger.warning(f"Resumen generado demasiado breve ({len(summary_content)} caracteres) para un contexto de {len(context_text)} caracteres")
                # Intentar nuevamente con un prompt más específico
                retry_prompt = f"""
                IMPORTANTE: Necesito un resumen COMPLETO y DETALLADO. El resumen anterior era demasiado breve.
                
                CONSULTA ORIGINAL: {query}
                
                CONTENIDO COMPLETO A RESUMIR:
                {context_text}
                
                Por favor, genera un resumen extenso y completo que conserve TODOS los detalles importantes,
                cifras, recomendaciones y estructura. El resumen debe tener suficiente detalle para reemplazar 
                al texto original.
                """
                
                retry_messages = [
                    SystemMessage(content="Eres un especialista en generar resúmenes DETALLADOS y COMPLETOS que preservan toda la información importante."),
                    HumanMessage(content=retry_prompt)
                ]
                
                retry_response = self.invoke_llm(retry_messages, prompt_type="langchain")
                summary_content = retry_response.content
            
            # También intentar obtener artículos relevantes
            try:
                mcp_result = self.mcp_client.call_tool_sync("search_articles", {"query": query})
                articles = mcp_result.get("result", [])
                
                if articles and isinstance(articles, list) and len(articles) > 0:
                    # Añadir enlaces a artículos relevantes al final del resumen
                    summary_content += "\n\nFuentes adicionales relevantes:\n"
                    for i, article in enumerate(articles[:3], 1):  # Limitar a 3 artículos
                        if isinstance(article, dict):
                            title = article.get("title", "Artículo sin título")
                            summary_content += f"{i}. {title}\n"
            except Exception as e:
                logger.warning(f"No se pudieron obtener artículos relevantes: {str(e)}")
            
            # Registrar el resumen generado para ayudar en depuración
            logger.info(f"Resumen generado de longitud: {len(summary_content)}")
            logger.info(f"Extracto del resumen: {summary_content[:200]}...")
            
            processing_time = time.time() - start_time
            
            # Determinar la fuente original del contenido
            source = "unknown"
            if isinstance(context, dict):
                if "source" in context:
                    source = context["source"]
                elif "current_agent" in context:
                    source = context["current_agent"]
            
            return {
                "result": {
                    "content": summary_content,
                    "source": source,
                    "summarized_by": "summary_agent",
                    "processing_time": processing_time,
                    "query": query
                },
                "confidence": 0.9,
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
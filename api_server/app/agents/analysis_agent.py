from typing import Dict, Any
import time
from langchain_core.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.core.logging import logger
from app.core.config import get_settings
from langchain_openai import ChatOpenAI
import os
from pathlib import Path
from app.tools.mcp_client import MCPClient
import json

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
        
        # Inicializar cliente MCP
        try:
            # Deducir la ruta del servidor MCP
            mcp_path = str(Path(os.path.abspath(__file__)).parents[3] / "mcp_server" / "main.py")
            self.mcp_client = MCPClient(
                base_url=settings.MCP_CLIENT_URL,
                use_stdio=True,
                mcp_server_path=mcp_path
            )
            
            # Volver a intentar obtener el cliente global después de inicializar
            from app.agents.mcp_integration import _mcp_client, get_mcp_tools_sync
            
            # Inicializar con get_mcp_tools_sync para asegurar cliente global
            tools_list = get_mcp_tools_sync()
            
            if tools_list:
                self.mcp_client = _mcp_client  # Actualizar referencia al cliente global
                self.mcp_initialized = True
                
                # Actualizar lista de herramientas disponibles
                self.available_mcp_tools = [tool["name"] for tool in tools_list]
                logger.info(f"Cliente MCP inicializado. Herramientas disponibles: {', '.join(self.available_mcp_tools)}")
            else:
                logger.warning("No se pudo inicializar el cliente MCP")
                self.mcp_initialized = False
                self.available_mcp_tools = []
        except Exception as e:
            logger.error(f"Error al inicializar el cliente MCP: {str(e)}")
            self.mcp_client = None
            self.mcp_initialized = False
            self.available_mcp_tools = []
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
        context = input_data.get("context", {})
        
        # Loguear la consulta con un límite seguro
        query_preview = query[:50] + "..." if len(query) > 50 else query
        logger.info(f"AnalysisAgent procesando consulta: {query_preview}")
        
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
        
        # Obtener datos adicionales mediante MCP si está disponible
        mcp_data = {}
        try:
            # Inicializar MCP si es necesario
            if hasattr(self, 'mcp_client') and self.mcp_client is not None:
                self.mcp_client.initialize_sync()
            
            # Usar LLM para categorizar el tipo de análisis necesario
            if self.llm:
                categorization_prompt = f"""
                Analiza la siguiente consulta y determina qué tipo de análisis se necesita realizar.
                
                Consulta: "{query}"
                
                Devuelve SOLAMENTE un objeto JSON con esta estructura:
                {{
                    "analysis_type": "trend_analysis" | "article_search" | "general",
                    "parameters": {{
                        // Parámetros específicos según el tipo de análisis
                    }}
                }}
                
                Si es un análisis de tendencia (trend_analysis), incluye:
                - has_numerical_data: true/false
                - data_source: dónde se encuentran los datos numéricos
                
                Si es una búsqueda de artículos (article_search), incluye:
                - search_query: la consulta de búsqueda refinada
                
                No incluyas texto adicional en tu respuesta, solo el JSON.
                """
                
                try:
                    response = self.llm.invoke(categorization_prompt)
                    categorization = json.loads(response.content.strip())
                    logger.info(f"Categorización por LLM: {categorization}")
                    
                    analysis_type = categorization.get("analysis_type", "general")
                    parameters = categorization.get("parameters", {})
                    
                    # Ejecutar herramientas basadas en la categorización del LLM
                    if analysis_type == "trend_analysis" and parameters.get("has_numerical_data", False):
                        # Buscar los datos numéricos en el contexto o en la consulta
                        numerical_data = context.get("datos", [])
                        
                        # Si hay datos numéricos, realizar análisis de tendencia
                        if numerical_data and isinstance(numerical_data, list):
                            # Verificar que existe el cliente MCP
                            if not hasattr(self, 'mcp_client') or self.mcp_client is None:
                                # Intenta usar el cliente global como fallback
                                from app.agents.mcp_integration import _mcp_client
                                if _mcp_client and hasattr(_mcp_client, 'call_tool_sync'):
                                    logger.info(f"Usando cliente MCP global como fallback")
                                    trend_result = _mcp_client.call_tool_sync("analizar_tendencia", {
                                        "datos": numerical_data,
                                        "etiquetas": context.get("etiquetas", [])
                                    })
                                else:
                                    logger.error(f"No hay cliente MCP disponible para ejecutar 'analizar_tendencia'")
                                    trend_result = None
                            else:
                                # Usar el cliente propio del agente
                                trend_result = self.mcp_client.call_tool_sync("analizar_tendencia", {
                                    "datos": numerical_data,
                                    "etiquetas": context.get("etiquetas", [])
                                })
                            
                            if trend_result and "error" not in trend_result:
                                mcp_data["tendencia"] = trend_result.get("result", {})
                                logger.info("Datos de tendencia obtenidos de MCP")
                    
                    # Para cualquier tipo de análisis, considerar búsqueda de artículos relevantes
                    search_query = parameters.get("search_query", query)
                    
                    # Verificar que existe el cliente MCP
                    if not hasattr(self, 'mcp_client') or self.mcp_client is None:
                        # Intenta usar el cliente global como fallback
                        from app.agents.mcp_integration import _mcp_client
                        if _mcp_client and hasattr(_mcp_client, 'call_tool_sync'):
                            logger.info(f"Usando cliente MCP global como fallback")
                            search_result = _mcp_client.call_tool_sync("search_articles", {"query": search_query})
                        else:
                            logger.error(f"No hay cliente MCP disponible para ejecutar 'search_articles'")
                            search_result = None
                    else:
                        # Usar el cliente propio del agente
                        search_result = self.mcp_client.call_tool_sync("search_articles", {"query": search_query})
                    
                    if search_result and "error" not in search_result:
                        mcp_data["articles"] = search_result.get("result", {})
                        logger.info("Datos de artículos obtenidos de MCP")
                    
                except Exception as e:
                    logger.error(f"Error al procesar la categorización con LLM: {str(e)}")
                    # Caer en el enfoque anterior como fallback
                    mcp_data = self._legacy_get_mcp_data(query, context)
            else:
                # Si no hay LLM disponible, usar el enfoque anterior
                mcp_data = self._legacy_get_mcp_data(query, context)
            
        except Exception as e:
            logger.error(f"Error al obtener datos de MCP: {str(e)}")
        
        # Crear el mensaje con el sistema de prompt
        from langchain_core.messages import SystemMessage, HumanMessage
        
        # Preparar el contenido del prompt
        system_content = """Eres un agente especializado en análisis detallado de datos y textos.
        Tu objetivo es proporcionar análisis profundos, identificar patrones, y extraer insights valiosos.
        
        Debes:
        1. Analizar el contenido en detalle
        2. Identificar patrones y tendencias
        3. Extraer conclusiones relevantes
        4. Proporcionar recomendaciones basadas en el análisis
        
        Formatea tu respuesta de manera clara y estructurada."""
        
        # Preparar el mensaje de usuario con contexto adicional
        user_content = query
        if mcp_data:
            user_content += "\n\nDatos adicionales disponibles:\n"
            if "tendencia" in mcp_data:
                tendencia = mcp_data["tendencia"]
                user_content += f"\nAnálisis de tendencia: {tendencia.get('analisis', 'No disponible')}\n"
                if "tendencia" in tendencia:
                    trend_data = tendencia["tendencia"]
                    user_content += f"- Dirección: {trend_data.get('direccion', 'No disponible')}\n"
                    user_content += f"- Cambio porcentual: {trend_data.get('cambio_porcentual', 'No disponible')}\n"
            
            if "articles" in mcp_data:
                articles = mcp_data["articles"]
                if isinstance(articles, list):
                    user_content += "\nArtículos relevantes:\n"
                    for i, article in enumerate(articles[:3], 1):  # Limitamos a 3 artículos
                        user_content += f"{i}. {article.get('title', 'Sin título')}\n"
                        user_content += f"   Resumen: {article.get('summary', 'No disponible')[:100]}...\n"
        
        # Crear los mensajes para el LLM
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=user_content)
        ]
        
        try:
            # Invocar el LLM usando el método con logging
            response = self.invoke_llm(messages, prompt_type="langchain")
            
            if not response or not hasattr(response, 'content'):
                raise ValueError("El LLM no generó una respuesta válida")
                
            result = response.content
            confidence = 0.75  # Nivel de confianza para análisis
            
            # Calcular tiempo de procesamiento
            processing_time = time.time() - start_time
            
            return {
                "result": result,
                "input": query,
                "context": context,
                "mcp_data": mcp_data,
                "confidence": confidence,
                "processing_time": processing_time,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error al generar análisis: {str(e)}")
            processing_time = time.time() - start_time
            
            return {
                "result": f"Error al procesar la consulta de análisis: {str(e)}",
                "input": query,
                "confidence": 0.0,
                "processing_time": processing_time,
                "success": False,
                "error": str(e)
            } 

    def _legacy_get_mcp_data(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método legacy para obtener datos de MCP sin usar LLM para categorización.
        
        Args:
            query: La consulta del usuario
            context: El contexto adicional
            
        Returns:
            Diccionario con los datos obtenidos de MCP
        """
        mcp_data = {}
        try:
            # Invocar la herramienta MCP 'analizar_tendencia' si es relevante
            if "datos" in context and isinstance(context["datos"], list):
                # Verificar que existe el cliente MCP
                if not hasattr(self, 'mcp_client') or self.mcp_client is None:
                    # Intenta usar el cliente global como fallback
                    from app.agents.mcp_integration import _mcp_client
                    if _mcp_client and hasattr(_mcp_client, 'call_tool_sync'):
                        logger.info(f"Usando cliente MCP global como fallback")
                        trend_result = _mcp_client.call_tool_sync("analizar_tendencia", {
                            "datos": context["datos"],
                            "etiquetas": context.get("etiquetas", [])
                        })
                    else:
                        logger.error(f"No hay cliente MCP disponible para ejecutar 'analizar_tendencia'")
                        trend_result = None
                else:
                    # Usar el cliente propio del agente
                    trend_result = self.mcp_client.call_tool_sync("analizar_tendencia", {
                        "datos": context["datos"],
                        "etiquetas": context.get("etiquetas", [])
                    })
                
                if trend_result and "error" not in trend_result:
                    mcp_data["tendencia"] = trend_result.get("result", {})
                    logger.info("Datos de tendencia obtenidos de MCP")
            
            # Invocar la herramienta MCP 'search_articles' si es una consulta de búsqueda
            # Verificar que existe el cliente MCP
            if not hasattr(self, 'mcp_client') or self.mcp_client is None:
                # Intenta usar el cliente global como fallback
                from app.agents.mcp_integration import _mcp_client
                if _mcp_client and hasattr(_mcp_client, 'call_tool_sync'):
                    logger.info(f"Usando cliente MCP global como fallback")
                    search_result = _mcp_client.call_tool_sync("search_articles", {"query": query})
                else:
                    logger.error(f"No hay cliente MCP disponible para ejecutar 'search_articles'")
                    search_result = None
            else:
                # Usar el cliente propio del agente
                search_result = self.mcp_client.call_tool_sync("search_articles", {"query": query})
            
            if search_result and "error" not in search_result:
                mcp_data["articles"] = search_result.get("result", {})
                logger.info("Datos de artículos obtenidos de MCP")
            
        except Exception as e:
            logger.error(f"Error en el procesamiento legacy de MCP: {str(e)}")
        
        return mcp_data 
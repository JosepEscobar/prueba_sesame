from typing import Any, Dict, Optional
import time
import json

from langchain_openai import ChatOpenAI 
from app.agents.base import BaseAgent
from app.core.logging import logger
from app.core.metrics import MetricsCollector
from app.core.config import get_settings
from app.tools.mcp_client import MCPClient
from app.agents.mcp_integration import configure_agent_with_mcp, get_mcp_tools

# Obtener la configuración
settings = get_settings()

class MarketingAgent(BaseAgent):
    """
    Agente especializado en marketing y estrategias de mercado.
    
    Este agente proporciona recomendaciones y análisis sobre:
    - Desarrollo de estrategias de marketing
    - Análisis de mercado y competencia
    - Segmentación de clientes y buyer personas
    - Campañas de marketing digital
    - Optimización de canales de venta
    - Gestión de marca y posicionamiento
    - Estrategias de contenido y SEO
    - Análisis de datos de marketing y KPIs
    - Planificación de medios y presupuestos
    - Experiencia del cliente (CX) y marketing relacional
    """

    def __init__(self):
        """Inicializa el agente de marketing."""
        super().__init__(
            name="marketing_agent",
            description="Especialista en estrategias de marketing y análisis de mercado."
        )
        
        # Comprobar si hay una clave API válida
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-key-here":
            self.llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.3)
        else:
            # Crear un modelo ficticio para desarrollo
            logger.warning("No hay clave API de OpenAI válida. Usando respuestas ficticias para desarrollo.")
            self.llm = None
            
        # Inicializar el cliente MCP directo para llamadas específicas
        self.mcp_client = MCPClient(base_url=settings.MCP_CLIENT_URL)
        
        # Obtener herramientas MCP adaptadas para LangChain
        mcp_tools = get_mcp_tools()
        
        # Configurar el agente con herramientas MCP para LangChain
        configure_agent_with_mcp(self, mcp_tools)
        
        self.services = [
            "Estrategia de marketing",
            "Posicionamiento de marca",
            "Marketing digital",
            "Segmentación de mercado",
            "Análisis competitivo",
            "Estrategia de contenidos",
            "Optimización de canales",
            "Análisis de audiencia",
            "Customer journey",
            "Planificación de campañas"
        ]
        logger.info(f"Agente {self.name} inicializado con {len(self.services)} servicios y herramientas MCP")

    def _execute_impl(self, input_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Implementa la lógica de ejecución del agente de marketing.
        
        Args:
            input_data: Datos de entrada que contienen la consulta de marketing y contexto
            
        Returns:
            Diccionario con el resultado del análisis de marketing, input original y nivel de confianza
        """
        start_time = time.time()
        query = input_data.get("query", "")
        context = input_data.get("context", {})
        
        # Logueamos solo los primeros 50 caracteres de la consulta como texto, no como slice
        query_preview = query[:50] + "..." if len(query) > 50 else query
        logger.info(f"Procesando consulta de marketing: {query_preview}")
        
        # Si no hay un LLM configurado (por falta de API key), devolver un error
        if self.llm is None:
            logger.error("Error: No hay clave API de OpenAI válida. Imposible generar respuesta.")
            processing_time = time.time() - start_time
            return {
                "result": "",
                "input": query,
                "confidence": 0.0,
                "processing_time": processing_time,
                "success": False,
                "error": "No se ha configurado una clave API de OpenAI válida. Para utilizar este agente, configure la clave en el archivo .env"
            }
        
        # Recopilar datos de marketing relevantes usando herramientas MCP
        marketing_data = {}
        
        try:
            # Inicializar el cliente MCP (esto creará una tarea en segundo plano si es necesario)
            initialized = self.mcp_client.initialize_sync()
            
            if initialized:
                logger.info("Cliente MCP inicializado correctamente. Buscando datos con herramientas MCP.")
                
                # Ejemplo: Usar directamente la herramienta data_lookup a través de MCP
                try:
                    # Usar herramienta de análisis de mercado si está disponible
                    try:
                        # Llamar a la herramienta analizar_tendencia del MCP server
                        trend_params = {
                            "datos": [100, 120, 150, 130, 170],
                            "etiquetas": ["Ene", "Feb", "Mar", "Abr", "May"]
                        }
                        trend_data = self.mcp_client.call_tool_sync("analizar_tendencia", trend_params)
                        marketing_data["trend_analysis"] = trend_data
                        logger.info("Análisis de tendencia obtenido a través de MCP")
                    except Exception as e:
                        logger.error(f"Error al obtener análisis de tendencia: {str(e)}")
                    
                    # Usar la herramienta de recomendación de estrategia de marketing si está disponible
                    if "industry" in context:
                        try:
                            strategy_params = {
                                "industria": context["industry"],
                                "presupuesto": context.get("budget", 50000),
                                "objetivo": context.get("goal", "awareness"),
                                "publico_objetivo": context.get("target_audience", "general")
                            }
                            strategy_data = self.mcp_client.call_tool_sync("recomendar_estrategia_marketing", strategy_params)
                            marketing_data["marketing_strategy"] = strategy_data
                            logger.info(f"Estrategia de marketing obtenida para {context['industry']}")
                        except Exception as e:
                            logger.error(f"Error al obtener estrategia de marketing: {str(e)}")
                    
                    # Analizar rendimiento de campaña si hay datos disponibles
                    if "campaign_data" in context and isinstance(context["campaign_data"], dict):
                        try:
                            campaign_data = context["campaign_data"]
                            campaign_params = {
                                "nombre_campania": campaign_data.get("name", "Campaña sin nombre"),
                                "impresiones": campaign_data.get("impressions", 0),
                                "clics": campaign_data.get("clicks", 0),
                                "conversiones": campaign_data.get("conversions", 0),
                                "coste": campaign_data.get("cost", 0)
                            }
                            campaign_analysis = self.mcp_client.call_tool_sync("analizar_rendimiento_campania", campaign_params)
                            marketing_data["campaign_analysis"] = campaign_analysis
                            logger.info(f"Análisis de campaña obtenido para {campaign_params['nombre_campania']}")
                        except Exception as e:
                            logger.error(f"Error al obtener análisis de campaña: {str(e)}")
                    
                except Exception as e:
                    logger.error(f"Error al obtener datos mediante MCP: {str(e)}")
                    
            else:
                logger.warning("No se pudo inicializar el cliente MCP. Usando método alternativo.")
                # Usar el servicio local si está disponible como fallback
                data_service = self.get_tool("data_lookup")
                if data_service:
                    logger.info("Utilizando servicio local de búsqueda de datos como fallback")
                    # Usar el servicio local como fallback
                    # ... (código existente para usar data_service) ...
        except Exception as e:
            logger.error(f"Error al inicializar cliente MCP: {str(e)}")
            # Usar fallback si está disponible
            data_service = self.get_tool("data_lookup")
            if data_service:
                # ... código de fallback existente ...
                pass
        
        # Usar también otras herramientas MCP si es necesario
        try:
            # Ejemplo: Usar herramienta financial_models para tendencias de mercado
            if "industry" in context:
                financial_params = {
                    "industry": context["industry"],
                    "model_type": "market_trends",
                    "complexity": "simple"
                }
                financial_data = self.mcp_client.call_tool_sync("financial_models", financial_params)
                marketing_data["market_trends"] = financial_data
                logger.info(f"Datos financieros obtenidos a través de MCP para industria: {context['industry']}")
        except Exception as e:
            logger.error(f"Error al obtener datos financieros mediante MCP: {str(e)}")
        
        # Preparar input para el prompt con todos los datos recopilados
        prompt_input = {
            "query": query,
            "context": context,
            "marketing_data": marketing_data,
            "services": self.services
        }
        
        # Formatear el prompt usando el método de formato
        formatted_prompt = self._format_marketing_prompt(prompt_input)
        
        # Generar análisis de marketing utilizando el LLM
        logger.info("Generando análisis de marketing con el LLM")
        response = self.llm.invoke(formatted_prompt)
        
        # Estructurar la respuesta
        processing_time = time.time() - start_time
        
        # Recopilar fuentes de datos utilizadas
        data_sources = []
        if "recent_news" in marketing_data and isinstance(marketing_data["recent_news"], dict):
            source = marketing_data["recent_news"].get("source")
            if source:
                data_sources.append({"type": "news", "source": source})
                
        if "industry_reports" in marketing_data and isinstance(marketing_data["industry_reports"], dict):
            source = marketing_data["industry_reports"].get("source")
            if source:
                data_sources.append({"type": "report", "source": source})
        
        result = {
            "result": {
                "content": response.content,
                "data_sources": data_sources,
                "marketing_data_summary": self._summarize_marketing_data(marketing_data),
                "using_mcp": True
            },
            "agent": "marketing",
            "input": input_data.get("query", ""),
            "confidence": 0.87,  # Nivel de confianza para respuestas de marketing
            "processing_time": processing_time,
            "model": "gpt-3.5-turbo"
        }
        
        logger.info(f"Análisis de marketing completado en {processing_time:.2f} segundos utilizando herramientas MCP")
        
        return result
    
    def _format_marketing_prompt(self, input_data: Dict[str, Any]) -> str:
        """
        Formatea el prompt para el modelo de lenguaje.
        
        Args:
            input_data: Datos preparados para el prompt
            
        Returns:
            Prompt formateado
        """
        query = input_data.get("query", "")
        context = input_data.get("context", {})
        marketing_data = input_data.get("marketing_data", {})
        services = input_data.get("services", [])
        
        prompt = f"""
        Eres un experto en marketing y estrategia comercial actuando como parte de un sistema 
        de asistencia empresarial. Debes proporcionar un análisis de marketing detallado y 
        recomendaciones prácticas basadas en la siguiente consulta y datos disponibles.
        
        ## Consulta del cliente:
        {query}
        
        ## Contexto adicional:
        {context}
        
        ## Datos de marketing disponibles:
        {marketing_data}
        
        ## Tus áreas de especialización:
        {', '.join(services)}
        
        ## Instrucciones:
        1. Analiza detenidamente toda la información de marketing proporcionada
        2. Identifica oportunidades e insights relevantes para la consulta
        3. Formula recomendaciones de marketing concretas y accionables
        4. Considera el posicionamiento de marca y la propuesta de valor
        5. Incluye consideraciones sobre canales, mensajes y audiencia
        6. Proporciona ejemplos o casos de estudio relevantes cuando sea posible
        
        ## Formato de respuesta:
        Tu análisis debe seguir esta estructura:
        1. Resumen ejecutivo de la estrategia de marketing (breve)
        2. Análisis de la situación actual y oportunidades
        3. Recomendaciones estratégicas y tácticas de marketing
        4. Canales y mensajes recomendados
        5. Métricas de marketing a monitorear (KPIs)
        6. Próximos pasos recomendados
        
        Responde de manera profesional, basada en datos, y orientada a resultados.
        """
        
        return prompt 

    def _summarize_marketing_data(self, marketing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera un resumen de los datos de marketing obtenidos para incluir en la respuesta.
        
        Args:
            marketing_data: Datos de marketing completos
            
        Returns:
            Resumen de los datos de marketing
        """
        summary = {}
        
        if "recent_news" in marketing_data:
            summary["news_available"] = True
            if isinstance(marketing_data["recent_news"], dict) and "source" in marketing_data["recent_news"]:
                summary["news_source"] = marketing_data["recent_news"]["source"]
                
        if "industry_reports" in marketing_data:
            summary["industry_reports_available"] = True
            
        if "market_demographics" in marketing_data:
            summary["demographics_available"] = True
            
        if "web_resources" in marketing_data:
            summary["web_resources_available"] = True
            
        if "competitors_info" in marketing_data:
            summary["competitors_info_available"] = True
            summary["competitors_count"] = len(marketing_data["competitors_info"]) if isinstance(marketing_data["competitors_info"], dict) else 0
            
        if "market_trends" in marketing_data:
            summary["market_trends_available"] = True
            
        return summary 
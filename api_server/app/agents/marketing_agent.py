import json
import time
from typing import Any

from langchain_openai import ChatOpenAI

from app.agents.base import BaseAgent
from app.agents.mcp_integration import configure_agent_with_mcp, get_mcp_tools_sync
from app.core.config import get_settings
from app.core.logging import logger
from app.tools.mcp_client import MCPClient

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
            name="marketing_agent", description="Especialista en estrategias de marketing y análisis de mercado."
        )

        # Comprobar si hay una clave API válida
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-key-here":
            self.llm = ChatOpenAI(model_name="gpt-4.1-mini", temperature=0.3)
        else:
            # Crear un modelo ficticio para desarrollo
            logger.warning("No hay clave API de OpenAI válida. Usando respuestas ficticias para desarrollo.")
            self.llm = None

        # Inicializar el cliente MCP directo para llamadas específicas
        self.mcp_client = MCPClient(base_url=settings.MCP_CLIENT_URL)

        # Obtener herramientas MCP adaptadas para LangChain
        try:
            mcp_tools = get_mcp_tools_sync()
            # Configurar el agente con herramientas MCP para LangChain
            configure_agent_with_mcp(self, mcp_tools)

            # Volver a intentar obtener el cliente global después de inicializar
            from app.agents.mcp_integration import _mcp_client

            self.mcp_client = _mcp_client  # Asignar el cliente global a self.mcp_client

            if self.mcp_client is not None:
                self.available_mcp_tools = [tool["name"] for tool in mcp_tools]
                logger.info(
                    f"Cliente MCP inicializado. Herramientas disponibles: {', '.join(self.available_mcp_tools)}"
                )
                self.mcp_initialized = True
            else:
                logger.warning("Cliente MCP global es None después de inicialización")
                self.available_mcp_tools = []
                self.mcp_initialized = False
        except Exception as e:
            logger.error(f"Error al configurar herramientas MCP: {str(e)}")
            self.mcp_initialized = False
            self.available_mcp_tools = []

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
            "Planificación de campañas",
        ]
        logger.info(f"Agente {self.name} inicializado con {len(self.services)} servicios y herramientas MCP")

    def _execute_impl(self, input_data: dict[str, Any]) -> dict[str, Any]:
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

        # Logueamos la consulta
        query_preview = query[:50] + "..." if len(query) > 50 else query
        logger.info(f"Procesando consulta de marketing: {query_preview}")

        # Inicializar el cliente MCP para acceder a herramientas externas
        try:
            # Inicializar el cliente MCP si es necesario
            if hasattr(self, "mcp_client") and self.mcp_client is not None:
                initialized = self.mcp_client.initialize_sync()

                if initialized:
                    logger.info("Cliente MCP inicializado correctamente. Accediendo a herramientas de marketing.")

                    # Usar LLM para categorizar y extraer parámetros de la consulta de marketing
                    if self.llm:
                        categorization_prompt = f"""
                        Analiza la siguiente consulta de marketing y extrae los parámetros relevantes.

                        Consulta: "{query}"

                        Devuelve SOLAMENTE un objeto JSON con esta estructura:
                        {{
                            "marketing_actions": [
                                "strategy",
                                "trend_analysis",
                                "campaign_analysis",
                                "financial_analysis"
                            ],
                            "parameters": {{
                                "industry": "nombre de la industria si se menciona",
                                "budget": número si se menciona un presupuesto,
                                "goal": "objetivo de marketing mencionado (awareness, conversiones, tráfico, etc.)",
                                "target_audience": "público objetivo mencionado",
                                "campaign": {{
                                    "name": "nombre de campaña si se menciona",
                                    "impressions": número de impresiones si se mencionan,
                                    "clicks": número de clics si se mencionan,
                                    "conversions": número de conversiones si se mencionan,
                                    "cost": costo si se menciona
                                }}
                            }}
                        }}

                        Cada acción debe ser incluida solo si es relevante para la consulta.
                        No incluyas texto adicional en tu respuesta, solo el JSON.
                        """

                        try:
                            response = self.llm.invoke(categorization_prompt)
                            categorization = json.loads(response.content.strip())
                            logger.info(f"Categorización por LLM: {categorization}")

                            marketing_actions = categorization.get("marketing_actions", [])
                            parameters = categorization.get("parameters", {})

                            # Inicializar el diccionario de datos de marketing
                            marketing_data = {}

                            # Procesar acciones de marketing basadas en la categorización
                            try:
                                # 1. Análisis de tendencias si está en las acciones
                                if "trend_analysis" in marketing_actions and context.get("datos"):
                                    try:
                                        trend_params = {
                                            "datos": context["datos"],
                                            "etiquetas": context.get("etiquetas", None),
                                        }

                                        # Verificar que existe el cliente MCP
                                        if not hasattr(self, "mcp_client") or self.mcp_client is None:
                                            # Intenta usar el cliente global como fallback
                                            from app.agents.mcp_integration import (
                                                _mcp_client,
                                            )

                                            if _mcp_client and hasattr(_mcp_client, "call_tool_sync"):
                                                logger.info("Usando cliente MCP global como fallback")
                                                trend_data = _mcp_client.call_tool_sync(
                                                    "analizar_tendencia", trend_params
                                                )
                                            else:
                                                logger.error(
                                                    "No hay cliente MCP disponible para ejecutar 'analizar_tendencia'"
                                                )
                                                raise ValueError("No hay cliente MCP disponible")
                                        else:
                                            # Usar el cliente propio del agente
                                            trend_data = self.mcp_client.call_tool_sync(
                                                "analizar_tendencia", trend_params
                                            )

                                        marketing_data["trend_analysis"] = trend_data
                                        logger.info("Análisis de tendencia obtenido a través de MCP")
                                    except Exception as e:
                                        logger.error(f"Error al obtener análisis de tendencia: {str(e)}")

                                # 2. Estrategia de marketing si está en las acciones
                                if "strategy" in marketing_actions and parameters.get("industry"):
                                    try:
                                        industry = parameters.get("industry")
                                        strategy_params = {
                                            "industria": industry,
                                            "presupuesto": parameters.get("budget", context.get("budget", 50000)),
                                            "objetivo": parameters.get("goal", context.get("goal", "awareness")),
                                            "publico_objetivo": parameters.get(
                                                "target_audience", context.get("target_audience", "general")
                                            ),
                                        }

                                        # Verificar que existe el cliente MCP
                                        if not hasattr(self, "mcp_client") or self.mcp_client is None:
                                            # Intenta usar el cliente global como fallback
                                            from app.agents.mcp_integration import (
                                                _mcp_client,
                                            )

                                            if _mcp_client and hasattr(_mcp_client, "call_tool_sync"):
                                                logger.info("Usando cliente MCP global como fallback")
                                                strategy_data = _mcp_client.call_tool_sync(
                                                    "recomendar_estrategia_marketing", strategy_params
                                                )
                                            else:
                                                logger.error(
                                                    "No hay cliente MCP disponible para ejecutar "
                                                    "'recomendar_estrategia_marketing'"
                                                )
                                                raise ValueError("No hay cliente MCP disponible")
                                        else:
                                            # Usar el cliente propio del agente
                                            strategy_data = self.mcp_client.call_tool_sync(
                                                "recomendar_estrategia_marketing", strategy_params
                                            )

                                        marketing_data["marketing_strategy"] = strategy_data
                                        logger.info(f"Estrategia de marketing obtenida para {industry}")
                                    except Exception as e:
                                        logger.error(f"Error al obtener estrategia de marketing: {str(e)}")

                                # 3. Análisis de campaña si está en las acciones
                                if "campaign_analysis" in marketing_actions and parameters.get("campaign"):
                                    try:
                                        campaign_data = parameters.get("campaign", {})
                                        if campaign_data:
                                            campaign_params = {
                                                "nombre_campania": campaign_data.get("name", "Campaña sin nombre"),
                                                "impresiones": campaign_data.get(
                                                    "impressions", context.get("impressions", 0)
                                                ),
                                                "clics": campaign_data.get("clicks", context.get("clicks", 0)),
                                                "conversiones": campaign_data.get(
                                                    "conversions", context.get("conversions", 0)
                                                ),
                                                "coste": campaign_data.get("cost", context.get("cost", 0)),
                                            }

                                            # Verificar que existe el cliente MCP
                                            if not hasattr(self, "mcp_client") or self.mcp_client is None:
                                                # Intenta usar el cliente global como fallback
                                                from app.agents.mcp_integration import (
                                                    _mcp_client,
                                                )

                                                if _mcp_client and hasattr(_mcp_client, "call_tool_sync"):
                                                    logger.info("Usando cliente MCP global como fallback")
                                                    campaign_analysis = _mcp_client.call_tool_sync(
                                                        "analizar_rendimiento_campania", campaign_params
                                                    )
                                                else:
                                                    logger.error(
                                                        "No hay cliente MCP disponible para ejecutar "
                                                        "'analizar_rendimiento_campania'"
                                                    )
                                                    raise ValueError("No hay cliente MCP disponible")
                                            else:
                                                # Usar el cliente propio del agente
                                                campaign_analysis = self.mcp_client.call_tool_sync(
                                                    "analizar_rendimiento_campania", campaign_params
                                                )

                                            marketing_data["campaign_analysis"] = campaign_analysis
                                            logger.info(
                                                f"Análisis de campaña obtenido para "
                                                f"{campaign_params['nombre_campania']}"
                                            )
                                    except Exception as e:
                                        logger.error(f"Error al obtener análisis de campaña: {str(e)}")

                                # 4. Análisis financiero para marketing si está en las acciones
                                if "financial_analysis" in marketing_actions and parameters.get("industry"):
                                    try:
                                        industry = parameters.get("industry")
                                        financial_params = {
                                            "industria": industry,
                                            "metodo": "analisis_rentabilidad",
                                            "datos": None,
                                        }

                                        # Verificar que existe el cliente MCP
                                        if not hasattr(self, "mcp_client") or self.mcp_client is None:
                                            # Intenta usar el cliente global como fallback
                                            from app.agents.mcp_integration import (
                                                _mcp_client,
                                            )

                                            if _mcp_client and hasattr(_mcp_client, "call_tool_sync"):
                                                logger.info("Usando cliente MCP global como fallback")
                                                financial_data = _mcp_client.call_tool_sync(
                                                    "financial_models", financial_params
                                                )
                                            else:
                                                logger.error(
                                                    "No hay cliente MCP disponible para ejecutar 'financial_models'"
                                                )
                                                raise ValueError("No hay cliente MCP disponible")
                                        else:
                                            # Usar el cliente propio del agente
                                            financial_data = self.mcp_client.call_tool_sync(
                                                "financial_models", financial_params
                                            )

                                        marketing_data["market_trends"] = financial_data
                                        logger.info(
                                            f"Datos financieros obtenidos a través de MCP para industria: {industry}"
                                        )
                                    except Exception as e:
                                        logger.error(f"Error al obtener datos financieros: {str(e)}")

                            except Exception as e:
                                logger.error(f"Error al procesar acciones de marketing: {str(e)}")

                        except Exception as e:
                            logger.error(f"Error al procesar la categorización con LLM: {str(e)}")
                            # Caer en el enfoque anterior como fallback
                            marketing_data = self._legacy_marketing_processing(query, context)
                    else:
                        # Si no hay LLM disponible, usar el enfoque anterior
                        marketing_data = self._legacy_marketing_processing(query, context)
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

        # Preparar input para el prompt con todos los datos recopilados
        prompt_input = {"query": query, "context": context, "marketing_data": marketing_data, "services": self.services}

        # Generar un prompt personalizado para el LLM
        formatted_prompt = self._format_marketing_prompt(prompt_input)

        # Crear mensajes para la llamada a LangChain
        from langchain_core.messages import HumanMessage, SystemMessage

        system_message = """Eres un experto en marketing y estrategias de mercado. 
Proporciona análisis detallados y recomendaciones estratégicas basadas en los datos disponibles.

Tu respuesta debe ser:
- Estratégica y orientada a objetivos
- Basada en los datos proporcionados
- Estructurada con secciones claras
- Accionable y específica

Incluye métricas relevantes cuando estén disponibles y destaca oportunidades clave para mejorar."""

        messages = [SystemMessage(content=system_message), HumanMessage(content=formatted_prompt)]

        try:
            # Invocar el LLM usando el nuevo método para logging
            response = self.invoke_llm(messages, prompt_type="langchain")

            if not response or not hasattr(response, "content"):
                raise ValueError("El LLM no generó una respuesta válida")

            result = response.content
            confidence = 0.85  # Alta confianza para consultas de marketing

            # Métricas para el resultado
            processing_time = time.time() - start_time

            # Recopilar fuentes de datos utilizadas
            data_sources = []
            if marketing_data:
                for source_name, _source_data in marketing_data.items():
                    data_sources.append({"type": source_name, "source": "MCP Server"})

            # Estructura de respuesta más sencilla
            return {
                "result": result,
                "input": query,
                "context": context,
                "marketing_data": self._summarize_marketing_data(marketing_data),
                "data_sources": data_sources,
                "confidence": confidence,
                "processing_time": processing_time,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error al generar respuesta de marketing: {str(e)}")
            processing_time = time.time() - start_time

            return {
                "result": f"Error al procesar la consulta de marketing: {str(e)}",
                "input": query,
                "confidence": 0.0,
                "processing_time": processing_time,
                "success": False,
                "error": str(e),
            }

    def _format_marketing_prompt(self, input_data: dict[str, Any]) -> str:
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
        {", ".join(services)}

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

    def _summarize_marketing_data(self, marketing_data: dict[str, Any]) -> dict[str, Any]:
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
            summary["competitors_count"] = (
                len(marketing_data["competitors_info"]) if isinstance(marketing_data["competitors_info"], dict) else 0
            )

        if "market_trends" in marketing_data:
            summary["market_trends_available"] = True

        return summary

    def _extract_industry(self, query: str) -> str:
        """
        Extrae la industria a partir del texto de la consulta.

        Args:
            query: Texto de la consulta del usuario

        Returns:
            Nombre de la industria extraída o 'tecnología' por defecto
        """
        # Palabras clave para detectar industrias comunes
        industrias = {
            "tecnología": [
                "tecnología",
                "tech",
                "software",
                "hardware",
                "aplicación",
                "app",
                "móvil",
                "web",
                "internet",
                "computadora",
                "informática",
            ],
            "finanzas": [
                "finanzas",
                "banco",
                "inversión",
                "seguros",
                "financiero",
                "contabilidad",
                "economía",
                "bolsa",
                "acciones",
            ],
            "salud": ["salud", "médico", "hospital", "farmacéutica", "medicina", "clínica", "sanitario", "healthcare"],
            "educación": [
                "educación",
                "enseñanza",
                "escuela",
                "universidad",
                "colegio",
                "formación",
                "académico",
                "aprendizaje",
            ],
            "retail": [
                "retail",
                "comercio",
                "tienda",
                "venta",
                "minorista",
                "ecommerce",
                "comercio electrónico",
                "supermercado",
            ],
            "manufactura": ["manufactura", "fábrica", "producción", "industrial", "fabricación", "maquinaria"],
            "energía": ["energía", "petróleo", "gas", "renovable", "solar", "eólica", "eléctrica", "combustible"],
            "turismo": [
                "turismo",
                "hotel",
                "viaje",
                "restaurante",
                "hospitality",
                "alojamiento",
                "vacación",
                "aerolínea",
            ],
            "entretenimiento": [
                "entretenimiento",
                "media",
                "cine",
                "música",
                "juego",
                "deporte",
                "televisión",
                "streaming",
            ],
            "agricultura": ["agricultura", "alimento", "cultivo", "ganadería", "agrícola", "alimentos", "comida"],
        }

        # Normalizar el texto a minúsculas
        query_lower = query.lower()

        # Buscar palabras clave en el texto
        for industria, keywords in industrias.items():
            for keyword in keywords:
                if keyword in query_lower:
                    logger.info(f"Industria detectada: {industria} (keyword: {keyword})")
                    return industria

        # Si no se detecta ninguna industria, devolver valor por defecto
        logger.info("No se detectó industria específica, usando valor por defecto: tecnología")
        return "tecnología"

    def _legacy_marketing_processing(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        """
        Método legacy para procesar consultas de marketing sin usar LLM para categorización.

        Args:
            query: La consulta del usuario
            context: El contexto adicional

        Returns:
            Diccionario con los datos de marketing obtenidos
        """
        marketing_data = {}

        try:
            # 1. Análisis de tendencias si hay datos
            if context.get("datos"):
                try:
                    trend_params = {"datos": context["datos"], "etiquetas": context.get("etiquetas", None)}

                    # Verificar que existe el cliente MCP
                    if not hasattr(self, "mcp_client") or self.mcp_client is None:
                        # Intenta usar el cliente global como fallback
                        from app.agents.mcp_integration import _mcp_client

                        if _mcp_client and hasattr(_mcp_client, "call_tool_sync"):
                            logger.info("Usando cliente MCP global como fallback")
                            trend_data = _mcp_client.call_tool_sync("analizar_tendencia", trend_params)
                        else:
                            logger.error("No hay cliente MCP disponible para ejecutar 'analizar_tendencia'")
                            raise ValueError("No hay cliente MCP disponible")
                    else:
                        # Usar el cliente propio del agente
                        trend_data = self.mcp_client.call_tool_sync("analizar_tendencia", trend_params)

                    marketing_data["trend_analysis"] = trend_data
                    logger.info("Análisis de tendencia obtenido a través de MCP")
                except Exception as e:
                    logger.error(f"Error al obtener análisis de tendencia: {str(e)}")

            # 2. Estrategia de marketing si hay industria
            if "industry" in context:
                try:
                    strategy_params = {
                        "industria": context["industry"],
                        "presupuesto": context.get("budget", 50000),
                        "objetivo": context.get("goal", "awareness"),
                        "publico_objetivo": context.get("target_audience", "general"),
                    }

                    # Verificar que existe el cliente MCP
                    if not hasattr(self, "mcp_client") or self.mcp_client is None:
                        # Intenta usar el cliente global como fallback
                        from app.agents.mcp_integration import _mcp_client

                        if _mcp_client and hasattr(_mcp_client, "call_tool_sync"):
                            logger.info("Usando cliente MCP global como fallback")
                            strategy_data = _mcp_client.call_tool_sync(
                                "recomendar_estrategia_marketing", strategy_params
                            )
                        else:
                            logger.error(
                                "No hay cliente MCP disponible para ejecutar 'recomendar_estrategia_marketing'"
                            )
                            raise ValueError("No hay cliente MCP disponible")
                    else:
                        # Usar el cliente propio del agente
                        strategy_data = self.mcp_client.call_tool_sync(
                            "recomendar_estrategia_marketing", strategy_params
                        )

                    marketing_data["marketing_strategy"] = strategy_data
                    logger.info(f"Estrategia de marketing obtenida para {context['industry']}")
                except Exception as e:
                    logger.error(f"Error al obtener estrategia de marketing: {str(e)}")

            # 3. Análisis de campaña si hay datos
            if "campaign_data" in context and isinstance(context["campaign_data"], dict):
                try:
                    campaign_data = context["campaign_data"]
                    campaign_params = {
                        "nombre_campania": campaign_data.get("name", "Campaña sin nombre"),
                        "impresiones": campaign_data.get("impressions", 0),
                        "clics": campaign_data.get("clicks", 0),
                        "conversiones": campaign_data.get("conversions", 0),
                        "coste": campaign_data.get("cost", 0),
                    }

                    # Verificar que existe el cliente MCP
                    if not hasattr(self, "mcp_client") or self.mcp_client is None:
                        # Intenta usar el cliente global como fallback
                        from app.agents.mcp_integration import _mcp_client

                        if _mcp_client and hasattr(_mcp_client, "call_tool_sync"):
                            logger.info("Usando cliente MCP global como fallback")
                            campaign_analysis = _mcp_client.call_tool_sync(
                                "analizar_rendimiento_campania", campaign_params
                            )
                        else:
                            logger.error("No hay cliente MCP disponible para ejecutar 'analizar_rendimiento_campania'")
                            raise ValueError("No hay cliente MCP disponible")
                    else:
                        # Usar el cliente propio del agente
                        campaign_analysis = self.mcp_client.call_tool_sync(
                            "analizar_rendimiento_campania", campaign_params
                        )

                    marketing_data["campaign_analysis"] = campaign_analysis
                    logger.info(f"Análisis de campaña obtenido para {campaign_params['nombre_campania']}")
                except Exception as e:
                    logger.error(f"Error al obtener análisis de campaña: {str(e)}")

            # 4. Análisis financiero para marketing si hay industria
            if "industry" in context:
                try:
                    financial_params = {
                        "industria": context["industry"],
                        "metodo": "analisis_rentabilidad",
                        "datos": None,
                    }

                    # Verificar que existe el cliente MCP
                    if not hasattr(self, "mcp_client") or self.mcp_client is None:
                        # Intenta usar el cliente global como fallback
                        from app.agents.mcp_integration import _mcp_client

                        if _mcp_client and hasattr(_mcp_client, "call_tool_sync"):
                            logger.info("Usando cliente MCP global como fallback")
                            financial_data = _mcp_client.call_tool_sync("financial_models", financial_params)
                        else:
                            logger.error("No hay cliente MCP disponible para ejecutar 'financial_models'")
                            raise ValueError("No hay cliente MCP disponible")
                    else:
                        # Usar el cliente propio del agente
                        financial_data = self.mcp_client.call_tool_sync("financial_models", financial_params)

                    marketing_data["market_trends"] = financial_data
                    logger.info(f"Datos financieros obtenidos a través de MCP para industria: {context['industry']}")
                except Exception as e:
                    logger.error(f"Error al obtener datos financieros: {str(e)}")

        except Exception as e:
            logger.error(f"Error en procesamiento legacy de marketing: {str(e)}")

        return marketing_data

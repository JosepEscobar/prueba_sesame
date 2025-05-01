import json
import os
import time
from pathlib import Path
from typing import Any

from langchain_openai import ChatOpenAI

from app.agents.base import BaseAgent
from app.core.ai_prompt_builder import AIPromptBuilder
from app.core.config import get_settings
from app.core.llm import parse_llm_json_response
from app.core.logging import logger
from app.tools.mcp_client import MCPClient

# Obtener configuración
settings = get_settings()


class DataLookupAgent(BaseAgent):
    """
    Agente especializado en búsqueda y recuperación de datos.

    Este agente se encarga de:
    - Buscar información relevante en fuentes de datos
    - Interpretar consultas y convertirlas en consultas estructuradas
    - Recuperar datos específicos según criterios
    - Proporcionar contexto adicional para otros agentes
    """

    def __init__(self):
        """Inicializa el agente de búsqueda de datos."""
        super().__init__(
            name="data_lookup_agent",
            description="Especialista en búsqueda y recuperación de datos de múltiples fuentes.",
        )

        # Comprobar si hay una clave API válida
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-key-here":
            self.llm = ChatOpenAI(model_name="gpt-4.1-mini", temperature=0.1)
        else:
            # Crear un modelo ficticio para desarrollo
            logger.warning("No hay clave API de OpenAI válida. Usando respuestas ficticias para desarrollo.")
            self.llm = None

        # Inicializar el cliente MCP con StdioTransport
        mcp_server_path = str(Path(os.path.abspath("mcp_server/main.py")))
        self.mcp_client = MCPClient(
            base_url=settings.MCP_CLIENT_URL,
            use_stdio=True,  # Activar StdioTransport
            mcp_server_path=mcp_server_path,
        )

        self.services = [
            "Búsqueda de datos financieros",
            "Búsqueda de noticias",
            "Búsqueda de tendencias",
            "Datos de mercado",
            "Información de empresas",
        ]
        logger.info(f"Agente {self.name} inicializado con {len(self.services)} servicios usando StdioTransport")

    def _execute_impl(self, input_data: dict[Any, Any]) -> dict[Any, Any]:
        """
        Implementa la lógica de ejecución del agente de búsqueda de datos.

        Args:
            input_data: Datos de entrada que contienen la consulta y el contexto

        Returns:
            Diccionario con los datos encontrados, input original y nivel de confianza
        """
        start_time = time.time()
        query = input_data.get("query", "")
        context = input_data.get("context", {})
        lookup_type = input_data.get("lookup_type", "general")

        # Logueamos solo los primeros 50 caracteres de la consulta como texto, no como slice
        query_preview = query[:50] + "..." if len(query) > 50 else query
        logger.info(f"Procesando consulta de datos ({lookup_type}): {query_preview}")

        # Preparar los datos para la búsqueda
        lookup_data = {}

        try:
            # Inicializar el cliente MCP
            initialized = self.mcp_client.initialize_sync()

            if initialized:
                logger.info("Cliente MCP inicializado correctamente con StdioTransport. Ejecutando búsqueda de datos.")

                # Usar LLM para categorizar y extraer parámetros de la consulta
                if self.llm:
                    # Definir la estructura JSON esperada
                    json_schema = {
                        "lookup_category": "financial | marketing | trends | general",
                        "parameters": {
                            "empresa": "nombre de empresa (para financial)",
                            "periodo": "periodo de análisis (para financial)",
                            "campaign": "nombre de campaña (para marketing)",
                            "metrics": {
                                "impressions": "número de impresiones (para marketing)",
                                "clicks": "número de clics (para marketing)",
                                "conversions": "número de conversiones (para marketing)",
                                "cost": "costo (para marketing)",
                            },
                            "numerical_data": "datos numéricos para análisis (para trends)",
                            "labels": "etiquetas para datos (para trends)",
                            "predict": "si se debe hacer predicción (para trends)",
                            "future_periods": "periodos futuros a predecir (para trends)",
                        },
                    }

                    # Ejemplo para guiar al modelo
                    example_json = {
                        "lookup_category": "financial",
                        "parameters": {"empresa": "Apple", "periodo": "Q2 2023"},
                    }

                    # Crear el constructor de prompts
                    prompt_builder = AIPromptBuilder(
                        role="especialista en búsqueda y recuperación de datos",
                        task="Analiza la consulta del usuario e identifica la categoría de datos a buscar y los parámetros relevantes.",
                        input_data=query,
                        schema=json_schema,
                        criteria="""
                        Analiza cuidadosamente la consulta e identifica la categoría de búsqueda:
                        - financial: para datos financieros, inversiones, empresas, etc.
                        - marketing: para campañas, métricas de marketing, etc.
                        - trends: para análisis de tendencias, predicciones, etc.
                        - general: para consultas generales no específicas
                        
                        Incluye solo los parámetros relevantes para la categoría identificada.
                        """,
                        examples=[example_json],
                    )

                    # Crear el prompt usando el builder
                    categorization_prompt = prompt_builder.build_json_prompt(query)

                    try:
                        response = self.llm.invoke(categorization_prompt)

                        # Usar la utilidad de parseo JSON seguro
                        default_value = {"lookup_category": "general", "parameters": {}}
                        categorization = parse_llm_json_response(response, default_value)

                        lookup_category = categorization.get("lookup_category", "general")
                        parameters = categorization.get("parameters", {})

                        # Procesar según la categoría identificada por el LLM
                        if lookup_category == "financial":
                            company = parameters.get("empresa", context.get("company"))
                            if company:
                                financial_params = {
                                    "empresa": company,
                                    "periodo": parameters.get("periodo", context.get("period", "actual")),
                                }
                                financial_data = self.mcp_client.call_tool_sync(
                                    "buscar_datos_financieros", financial_params
                                )
                                lookup_data["financial_data"] = financial_data
                                logger.info(f"Datos financieros obtenidos para: {company}")

                        elif lookup_category == "marketing":
                            campaign = parameters.get("campaign", context.get("campaign"))
                            metrics = parameters.get("metrics", context.get("metrics", {}))

                            if campaign and metrics:
                                marketing_params = {
                                    "nombre_campania": campaign,
                                    "impresiones": metrics.get("impressions", 1000),
                                    "clics": metrics.get("clicks", 50),
                                    "conversiones": metrics.get("conversions", 10),
                                    "coste": metrics.get("cost", 500),
                                }
                                marketing_data = self.mcp_client.call_tool_sync(
                                    "analizar_rendimiento_campania", marketing_params
                                )
                                lookup_data["marketing_data"] = marketing_data
                                logger.info(f"Datos de marketing obtenidos para: {campaign}")

                        # Siempre realizar una búsqueda general de datos
                        general_params = {"lookup_type": lookup_category, "query": query}
                        general_data = self.mcp_client.call_tool_sync("data_lookup", general_params)
                        lookup_data["general_data"] = general_data
                        logger.info(f"Búsqueda general completada para tipo: {lookup_category}")

                        # Procesar tendencias si están en la categorización
                        if lookup_category == "trends":
                            numerical_data = parameters.get("numerical_data", context.get("numerical_data"))

                            if numerical_data:
                                trends_params = {
                                    "datos": numerical_data,
                                    "etiquetas": parameters.get("labels", context.get("labels", None)),
                                }
                                trends_data = self.mcp_client.call_tool_sync("analizar_tendencia", trends_params)
                                lookup_data["trends_data"] = trends_data
                                logger.info("Análisis de tendencias completado")

                                # Si se solicita además predicción
                                if parameters.get("predict", context.get("predict", False)):
                                    predict_params = {
                                        "datos": numerical_data,
                                        "periodos_futuros": parameters.get(
                                            "future_periods", context.get("future_periods", 3)
                                        ),
                                    }
                                    prediction_data = self.mcp_client.call_tool_sync("predecir_valores", predict_params)
                                    lookup_data["prediction_data"] = prediction_data
                                    logger.info("Predicción de valores completada")

                    except Exception as e:
                        logger.error(f"Error al procesar la categorización con LLM: {str(e)}")
                        # Caer en el enfoque anterior como fallback
                        lookup_data = self._legacy_lookup_processing(query, context)
                else:
                    # Si no hay LLM disponible, usar el enfoque anterior
                    lookup_data = self._legacy_lookup_processing(query, context)
            else:
                logger.warning("No se pudo inicializar el cliente MCP. Usando método alternativo.")
                # Implementar lógica alternativa si es necesario

        except Exception as e:
            logger.error(f"Error al obtener datos mediante MCP: {str(e)}")
            # Implementar lógica alternativa si es necesario

        # Generar un resumen de los datos encontrados
        result_summary = self._generate_data_summary(query, lookup_data, lookup_type)

        # Estructurar la respuesta
        processing_time = time.time() - start_time

        result = {
            "result": {"content": result_summary, "lookup_data": lookup_data, "lookup_type": lookup_type},
            "agent": "data_lookup",
            "input": input_data.get("query", ""),
            "confidence": 0.85,  # Nivel de confianza para búsquedas de datos
            "processing_time": processing_time,
            "model": "gpt-4.1-mini" if self.llm else "direct_lookup",
        }

        logger.info(f"Búsqueda de datos completada en {processing_time:.2f} segundos")

        return result

    def _generate_data_summary(self, query: str, data: dict[str, Any], lookup_type: str) -> str:
        """
        Genera un resumen de los datos encontrados.

        Args:
            query: Consulta original
            data: Datos encontrados
            lookup_type: Tipo de búsqueda

        Returns:
            Resumen de los datos
        """
        if not self.llm:
            # Si no hay LLM, generar un resumen básico
            return f"Datos encontrados para consulta: {query}. Tipo: {lookup_type}."

        # Formatear los datos para el prompt
        formatted_data = json.dumps(data, indent=2, ensure_ascii=False)

        prompt = f"""
        Genera un resumen conciso de los siguientes datos encontrados para la consulta:

        Consulta: {query}
        Tipo de búsqueda: {lookup_type}

        Datos:
        {formatted_data}

        Proporciona solo los puntos más importantes y relevantes para la consulta.
        """

        # Generar el resumen usando el LLM
        response = self.llm.invoke(prompt)
        return response.content

    def _extract_entity(self, query: str, entity_type: str) -> str:
        """
        Extrae entidades de la consulta del usuario.

        Args:
            query: Consulta del usuario
            entity_type: Tipo de entidad a extraer (company, campaign, etc.)

        Returns:
            Entidad extraída o cadena vacía si no se encuentra
        """
        # En una implementación real se usaría NER o un LLM
        # Esta es una implementación simple basada en palabras clave

        query_lower = query.lower()

        if entity_type == "company":
            companies = ["apple", "microsoft", "google", "amazon", "tesla", "meta", "facebook"]
            for company in companies:
                if company in query_lower:
                    return company

        elif entity_type == "campaign":
            campaigns = ["black friday", "navidad", "verano", "primavera", "lanzamiento"]
            for campaign in campaigns:
                if campaign in query_lower:
                    return campaign

        # Si no encontramos nada, devolver una cadena vacía
        return ""

    def _legacy_lookup_processing(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        """
        Método legacy para procesar consultas sin usar LLM para categorización.
        Este método se usa como fallback cuando el LLM no está disponible o falla.

        Args:
            query: La consulta del usuario
            context: El contexto adicional

        Returns:
            Diccionario con los datos obtenidos de las herramientas
        """
        lookup_data = {}
        lookup_type = context.get("lookup_type", "general")

        try:
            # Determinar qué tipo de datos necesitamos buscar
            if lookup_type == "financial":
                # Buscar datos financieros específicos
                company = context.get("company", self._extract_entity(query, "company"))

                if company:
                    financial_params = {"empresa": company, "periodo": context.get("period", "actual")}
                    financial_data = self.mcp_client.call_tool_sync("buscar_datos_financieros", financial_params)
                    lookup_data["financial_data"] = financial_data
                    logger.info(f"Datos financieros obtenidos para: {company}")

            elif lookup_type == "marketing":
                # Buscar datos de marketing
                campaign = context.get("campaign", self._extract_entity(query, "campaign"))

                if campaign and "metrics" in context:
                    metrics = context["metrics"]
                    marketing_params = {
                        "nombre_campania": campaign,
                        "impresiones": metrics.get("impressions", 1000),
                        "clics": metrics.get("clicks", 50),
                        "conversiones": metrics.get("conversions", 10),
                        "coste": metrics.get("cost", 500),
                    }
                    marketing_data = self.mcp_client.call_tool_sync("analizar_rendimiento_campania", marketing_params)
                    lookup_data["marketing_data"] = marketing_data
                    logger.info(f"Datos de marketing obtenidos para: {campaign}")

            # Siempre realizar una búsqueda general de datos
            general_params = {"lookup_type": lookup_type, "query": query}
            general_data = self.mcp_client.call_tool_sync("data_lookup", general_params)
            lookup_data["general_data"] = general_data
            logger.info(f"Búsqueda general completada para tipo: {lookup_type}")

            # Si se solicitan tendencias y tenemos datos numéricos
            if lookup_type == "trends" and "numerical_data" in context:
                trends_params = {"datos": context["numerical_data"], "etiquetas": context.get("labels", None)}
                trends_data = self.mcp_client.call_tool_sync("analizar_tendencia", trends_params)
                lookup_data["trends_data"] = trends_data
                logger.info("Análisis de tendencias completado")

                # Si se solicita además predicción
                if context.get("predict", False):
                    predict_params = {
                        "datos": context["numerical_data"],
                        "periodos_futuros": context.get("future_periods", 3),
                    }
                    prediction_data = self.mcp_client.call_tool_sync("predecir_valores", predict_params)
                    lookup_data["prediction_data"] = prediction_data
                    logger.info("Predicción de valores completada")

        except Exception as e:
            logger.error(f"Error en el procesamiento legacy: {str(e)}")

        return lookup_data

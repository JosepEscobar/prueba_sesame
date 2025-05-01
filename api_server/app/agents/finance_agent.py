import os
import time
from typing import Any

from app.agents.base import BaseAgent
from app.agents.mcp_integration import configure_agent_with_mcp, get_mcp_tools_sync
from app.core.config import get_settings
from app.core.logging import logger

# Obtener la configuración
settings = get_settings()

class FinanceAgent(BaseAgent):
    """
    Agente especializado en finanzas, inversiones y análisis financiero.

    Este agente proporciona recomendaciones y análisis sobre:
    - Análisis financiero de empresas
    - Modelos y proyecciones financieras
    - Estrategias de inversión
    - Análisis de riesgo
    - Valoración de empresas
    - Planificación financiera
    - Optimización fiscal
    - Presupuestos y control de costos
    - Métricas y KPIs financieros
    """

    def __init__(self):
        """
        Inicializa el agente de finanzas.
        """
        super().__init__(
            name="finance_agent",
            description="Especialista en finanzas, análisis financiero y estrategias de inversión"
        )

        # Servicios que puede ofrecer el agente de finanzas
        self.services = [
            "Análisis financiero",
            "Modelos financieros",
            "Estrategias de inversión",
            "Evaluación de riesgos",
            "Planificación financiera",
            "Valoración de activos",
            "Presupuestos",
            "Análisis de costos",
            "Proyecciones financieras"
        ]

        # Configurar el cliente MCP (Model Context Protocol)
        try:
            # En lugar de crear un nuevo cliente, usar el global desde mcp_integration
            from app.agents.mcp_integration import _mcp_client

            if _mcp_client is None:
                # Si no existe un cliente global, deducir la ruta del servidor MCP
                from pathlib import Path
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = Path(current_dir).parent.parent.parent.parent
                mcp_server_path = os.path.join(project_root, "mcp_server", "main.py")

                # Inicializar el cliente MCP en mcp_integration
                tools = get_mcp_tools_sync()
                if tools:
                    # Volver a intentar obtener el cliente global después de inicializar
                    from app.agents.mcp_integration import _mcp_client
                    self.mcp_client = _mcp_client  # Asignar el cliente global a self.mcp_client

                    if self.mcp_client is not None:
                        self.available_mcp_tools = [tool["name"] for tool in tools]
                        logger.info(f"Cliente MCP inicializado. Herramientas disponibles: {', '.join(self.available_mcp_tools)}")
                        self.mcp_initialized = True
                    else:
                        logger.warning("Cliente MCP global es None después de inicialización")
                        self.available_mcp_tools = []
                        self.mcp_initialized = False
                else:
                    logger.warning("No se pudo inicializar el cliente MCP desde get_mcp_tools_sync")
                    self.available_mcp_tools = []
                    self.mcp_initialized = False
            else:
                # Usar el cliente global existente
                self.mcp_client = _mcp_client
                self.mcp_initialized = True
                tools = _mcp_client.list_tools_sync()
                self.available_mcp_tools = [tool["name"] for tool in tools]
                logger.info(f"Usando cliente MCP existente. Herramientas disponibles: {', '.join(self.available_mcp_tools)}")
        except Exception as e:
            logger.error(f"Error al configurar cliente MCP: {str(e)}")
            self.mcp_client = None
            self.mcp_initialized = False
            self.available_mcp_tools = []

        # Obtener herramientas MCP en formato LangChain
        try:
            mcp_tools = get_mcp_tools_sync()
            configure_agent_with_mcp(self, mcp_tools)
            logger.info(f"Agente {self.name} inicializado con {len(self.services)} servicios y herramientas MCP")
        except Exception as e:
            logger.error(f"Error al configurar agente con herramientas MCP: {str(e)}")

        logger.info(f"Agente {self.name} inicializado")

    def _execute_impl(self, input_data: dict[Any, Any]) -> dict[Any, Any]:
        """
        Ejecuta el análisis financiero.

        Args:
            input_data: Datos de entrada con la consulta y contexto

        Returns:
            Resultado del análisis financiero
        """
        start_time = time.time()

        try:
            # Obtener la consulta
            query = input_data.get("query", "")

            # Obtener contexto adicional si existe
            context = input_data.get("context", {})

            # Extraer la industria relevante de la consulta o el contexto
            industry = context.get("industry") if context and "industry" in context else self._extract_industry(query)

            # Obtener datos financieros si los hay
            financial_data = {}

            # Intentar extraer nombre de la empresa
            company_name = context.get("company") if context and "company" in context else self._extract_company(query)

            # Si tenemos nombre de empresa, intentar obtener sus datos financieros
            if company_name:
                try:
                    company_data = None
                    # Primero intentar con la herramienta MCP
                    if self.mcp_client:
                        tool_response = self.mcp_client.call_tool_sync(
                            "buscar_datos_financieros",
                            {"empresa": company_name}
                        )
                        if tool_response and isinstance(tool_response, dict) and "result" in tool_response:
                            company_data = tool_response["result"]

                    if company_data:
                        financial_data = self._summarize_financial_data(company_data)
                except Exception as e:
                    logger.warning(f"No se pudieron obtener datos financieros para {company_name}: {str(e)}")

            # Comprobar si tenemos acceso a LLM
            if self.llm is None:
                raise Exception("LLM no disponible para generar análisis financiero")

            # Construir el prompt para el modelo
            prompt_data = {
                "query": query,
                "context": context,
                "financial_data": financial_data
            }

            prompt = self._format_finance_prompt(prompt_data)

            # Realizar consulta al LLM
            from langchain_core.messages import HumanMessage, SystemMessage

            messages = [
                SystemMessage(content="Eres un analista financiero experto. Tu tarea es proporcionar análisis financieros precisos y recomendaciones basadas en datos."),
                HumanMessage(content=prompt)
            ]

            # Invocar el LLM
            response = self.invoke_llm(messages)

            # Procesar el tiempo y devolver resultado
            processing_time = time.time() - start_time

            return {
                "result": {
                    "content": response.content,
                    "source": "finance_agent",
                    "model_type": "openai",
                    "analysis_complete": True,
                    "industry": industry
                },
                "confidence": 0.9,
                "processing_time": processing_time,
                "reasoning": "Generado con OpenAI API"
            }

        except Exception as e:
            logger.error(f"Error al ejecutar FinanceAgent: {str(e)}")
            processing_time = time.time() - start_time

            # En caso de error, devolver detalles del error
            return {
                "error": str(e),
                "result": {
                    "content": f"Error al generar análisis financiero: {str(e)}",
                    "source": "finance_agent",
                    "model_type": "error",
                    "error": str(e)
                },
                "confidence": 0.0,
                "processing_time": processing_time,
                "reasoning": f"Error durante el procesamiento: {str(e)}"
            }

    def _format_finance_prompt(self, input_data: dict[str, Any]) -> str:
        """
        Formatea el prompt para el modelo de lenguaje.

        Args:
            input_data: Datos preparados para el prompt

        Returns:
            Prompt formateado
        """
        query = input_data.get("query", "")
        context = input_data.get("context", {})
        financial_data = input_data.get("financial_data", {})

        prompt = f"""
        Eres un experto financiero actuando como parte de un sistema de asistencia 
        empresarial. Debes proporcionar un análisis financiero detallado y 
        recomendaciones prácticas basadas en la siguiente consulta y datos disponibles.

        ## Consulta del cliente:
        {query}

        ## Contexto adicional:
        {context}

        ## Datos financieros disponibles:
        {financial_data}

        ## Tus áreas de especialización:
        - Análisis financiero sectorial
        - Valoración de empresas y proyectos
        - Proyecciones de crecimiento y rentabilidad
        - Métricas financieras clave (KPIs)
        - Modelos financieros para distintas industrias
        - Estrategias de inversión y financiamiento

        ## Instrucciones:
        1. Proporciona un análisis financiero detallado y estructurado
        2. Incluye métricas relevantes y proyecciones numéricas cuando sea posible
        3. Basa tus recomendaciones en datos objetivos y tendencias actuales
        4. Considera el contexto específico de la industria mencionada
        5. Organiza tu respuesta en secciones claras con títulos
        6. Incluye elementos visuales como tablas cuando sea útil

        ## Formato de respuesta:
        Tu análisis debe estar bien estructurado con:
        - Introducción al contexto financiero
        - Análisis de la situación actual
        - Proyecciones justificadas
        - Recomendaciones concretas
        - Consideración de riesgos
        - Conclusiones

        Proporciona un análisis completo y útil que permita tomar decisiones informadas.
        """

        return prompt

    def _extract_industry(self, query: str) -> str | None:
        """
        Extrae la industria mencionada en la consulta.
        Método simplificado para propósitos de ejemplo.

        Args:
            query: Consulta del usuario

        Returns:
            Nombre de la industria o None si no se identifica
        """
        industry_keywords = {
            "tecnología": ["tecnología", "software", "hardware", "informática", "digital"],
            "finanzas": ["banco", "finanzas", "financiero", "inversión", "bolsa"],
            "salud": ["salud", "farmacéutica", "hospital", "médico", "sanitario"],
            "comercio": ["retail", "comercio", "tienda", "ecommerce", "minorista"],
            "manufactura": ["manufactura", "fabricación", "industrial", "fábrica"],
            "energía": ["energía", "petróleo", "gas", "renovable", "electricidad"]
        }

        query_lower = query.lower()

        for industry, keywords in industry_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return industry

        return None

    def _summarize_financial_data(self, financial_data: dict[str, Any]) -> dict[str, Any]:
        """
        Genera un resumen de los datos financieros obtenidos para incluir en la respuesta.

        Args:
            financial_data: Datos financieros completos

        Returns:
            Resumen de los datos financieros
        """
        summary = {}

        if "market_data" in financial_data:
            summary["market_data_available"] = True
            if isinstance(financial_data["market_data"], dict) and "source" in financial_data["market_data"]:
                summary["market_data_source"] = financial_data["market_data"]["source"]

        if "financial_models" in financial_data:
            summary["models_available"] = True
            if isinstance(financial_data["financial_models"], dict) and "model_type" in financial_data["financial_models"]:
                summary["model_type"] = financial_data["financial_models"]["model_type"]

        if "financial_news" in financial_data:
            summary["news_available"] = True

        if "company_data" in financial_data:
            summary["company_data_available"] = True

        return summary

    def _extract_company(self, query: str) -> str:
        """
        Extrae el nombre de la empresa mencionada en la consulta.

        Args:
            query: Consulta del usuario

        Returns:
            Nombre de la empresa o cadena vacía si no se encuentra
        """
        # Implementación simple - en producción usaríamos NER o un modelo específico
        common_companies = ["Apple", "Tesla", "Amazon", "Google", "Microsoft", "Facebook", "IBM", "Intel"]

        for company in common_companies:
            if company.lower() in query.lower():
                return company

        return ""

from typing import Dict, Any, List, Optional
import time
import json
import os

from langchain_openai import ChatOpenAI
from app.agents.base import BaseAgent
from app.core.logging import logger
from app.core.metrics import MetricsCollector
from app.core.config import get_settings
from app.tools.mcp_client import MCPClient
from app.agents.mcp_integration import configure_agent_with_mcp, get_mcp_tools

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
        """Inicializa el agente de finanzas."""
        super().__init__(
            name="finance_agent",
            description="Especialista en finanzas, inversiones y análisis financiero."
        )
        
        # Comprobar si hay una clave API válida
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-key-here":
            self.llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)
        else:
            # Crear un modelo ficticio para desarrollo
            logger.warning("No hay clave API de OpenAI válida. Usando respuestas ficticias para desarrollo.")
            self.llm = None
            
        # Inicializar el cliente MCP con StdioTransport
        # Obtener la ruta del servidor MCP del settings o utilizar una ruta por defecto
        mcp_server_path = getattr(settings, "MCP_SERVER_PATH", None)
        if not mcp_server_path:
            # Intentar deducir la ruta relativa al directorio actual
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
            mcp_server_path = os.path.join(project_root, "mcp_server", "main.py")
            logger.info(f"Usando ruta deducida para servidor MCP: {mcp_server_path}")
        
        # Inicializar el cliente MCP directo para llamadas con MCPClient
        self.mcp_client = MCPClient(
            base_url=settings.MCP_CLIENT_URL, 
            use_stdio=True,
            mcp_server_path=mcp_server_path
        )
        
        # Inicializar herramientas MCP desde el principio
        try:
            success = self.mcp_client.initialize_sync()
            if success:
                tools = self.mcp_client.list_tools_sync()
                logger.info(f"Cliente MCP inicializado correctamente. Herramientas disponibles: {len(tools)}")
                self.available_mcp_tools = [tool["name"] for tool in tools]
                logger.info(f"Herramientas MCP disponibles: {', '.join(self.available_mcp_tools)}")
            else:
                logger.warning("No se pudo inicializar el cliente MCP durante la inicialización del agente")
                self.available_mcp_tools = []
        except Exception as e:
            logger.error(f"Error al inicializar el cliente MCP: {str(e)}")
            self.available_mcp_tools = []
        
        # Obtener herramientas MCP adaptadas para LangChain
        mcp_tools = get_mcp_tools()
        
        # Configurar el agente con herramientas MCP para LangChain
        configure_agent_with_mcp(self, mcp_tools)
        
        self.services = [
            "Análisis financiero",
            "Modelos financieros",
            "Estrategias de inversión",
            "Análisis de riesgo",
            "Valoración de empresas",
            "Planificación financiera",
            "Optimización fiscal",
            "Presupuestos",
            "Métricas financieras"
        ]
        logger.info(f"Agente {self.name} inicializado con {len(self.services)} servicios y herramientas MCP")
    
    def _execute_impl(self, input_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Implementa la lógica de ejecución del agente de finanzas.
        
        Args:
            input_data: Datos de entrada que contienen la consulta financiera y contexto
            
        Returns:
            Diccionario con el resultado del análisis financiero, input original y nivel de confianza
        """
        start_time = time.time()
        query = input_data.get("query", "")
        context = input_data.get("context", {})
        
        # Logueamos solo los primeros 50 caracteres de la consulta como texto, no como slice
        query_preview = query[:50] + "..." if len(query) > 50 else query
        logger.info(f"Procesando consulta financiera: {query_preview}")
        
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
        
        # Recopilar datos financieros relevantes utilizando herramientas MCP
        financial_data = {}
        mcp_tools_used = []
        
        # Reinicializar el cliente MCP si es necesario
        if not self.available_mcp_tools:
            try:
                logger.info("Reintentando inicialización del cliente MCP")
                success = self.mcp_client.initialize_sync()
                if success:
                    tools = self.mcp_client.list_tools_sync()
                    self.available_mcp_tools = [tool["name"] for tool in tools]
                    logger.info(f"Cliente MCP inicializado exitosamente. Herramientas disponibles: {', '.join(self.available_mcp_tools)}")
                else:
                    logger.warning("No se pudo reinicializar el cliente MCP")
            except Exception as e:
                logger.error(f"Error al reinicializar el cliente MCP: {str(e)}")
        
        # Función auxiliar para ejecutar una herramienta MCP con manejo de errores
        def execute_mcp_tool(tool_name, params, data_key):
            nonlocal financial_data, mcp_tools_used
            if tool_name not in self.available_mcp_tools:
                logger.warning(f"Herramienta '{tool_name}' no disponible en el servidor MCP")
                return False
            
            try:
                logger.info(f"Llamando a herramienta MCP '{tool_name}' con parámetros: {params}")
                result = self.mcp_client.call_tool_sync(tool_name, params)
                
                if "error" in result:
                    logger.error(f"Error al ejecutar '{tool_name}': {result['error']}")
                    return False
                
                financial_data[data_key] = result
                mcp_tools_used.append(tool_name)
                logger.info(f"Herramienta '{tool_name}' ejecutada exitosamente")
                return True
            except Exception as e:
                logger.error(f"Excepción al ejecutar '{tool_name}': {str(e)}")
                return False
        
        # Extraer información relevante de la consulta
        company = context.get("company", self._extract_company(query))
        industry = context.get("industry", self._extract_industry(query))
        period = context.get("period", "actual")
        
        # 1. Buscar datos financieros
        if company and "buscar_datos_financieros" in self.available_mcp_tools:
            execute_mcp_tool(
                "buscar_datos_financieros",
                {"empresa": company, "periodo": period},
                "company_financials"
            )
        
        # 2. Calcular ratios financieros si tenemos datos básicos
        if "company_financials" in financial_data and "datos" in financial_data["company_financials"] and "calcular_ratios_financieros" in self.available_mcp_tools:
            datos = financial_data["company_financials"]["datos"]
            execute_mcp_tool(
                "calcular_ratios_financieros",
                {
                    "ingresos": datos.get("ingresos", 0),
                    "beneficio_neto": datos.get("beneficio_neto", 0),
                    "activos_totales": datos.get("activos_totales", 0),
                    "pasivos_totales": datos.get("pasivos_totales", 0)
                },
                "financial_ratios"
            )
        
        # 3. Obtener estrategia de marketing si es relevante
        if industry and "recomendar_estrategia_marketing" in self.available_mcp_tools:
            execute_mcp_tool(
                "recomendar_estrategia_marketing",
                {
                    "industria": industry,
                    "presupuesto": context.get("budget", 50000),
                    "objetivo": context.get("goal", "conversiones"),
                    "publico_objetivo": context.get("target_audience", "empresas")
                },
                "marketing_strategy"
            )
        
        # 4. Analizar tendencia si hay datos históricos disponibles
        historical_data = context.get("historical_data")
        if historical_data and isinstance(historical_data, list) and "analizar_tendencia" in self.available_mcp_tools:
            execute_mcp_tool(
                "analizar_tendencia",
                {
                    "datos": historical_data,
                    "etiquetas": context.get("historical_labels", [f"P{i+1}" for i in range(len(historical_data))])
                },
                "trend_analysis"
            )
        
        # 5. Predecir valores futuros si es relevante
        if historical_data and isinstance(historical_data, list) and "predecir_valores" in self.available_mcp_tools:
            execute_mcp_tool(
                "predecir_valores",
                {
                    "datos": historical_data,
                    "periodos_futuros": context.get("forecast_periods", 3)
                },
                "forecast"
            )
        
        # Añadir información sobre las herramientas utilizadas
        financial_data["tools_used"] = mcp_tools_used
        
        # Preparar input para el prompt con todos los datos recopilados
        prompt_input = {
            "query": query,
            "context": context,
            "financial_data": financial_data,
            "services": self.services
        }
        
        # Formatear el prompt usando el método de formato
        formatted_prompt = self._format_finance_prompt(prompt_input)
        
        # Usar las herramientas MCP recopiladas para construir el contexto
        tools_context = []
        for tool in mcp_tools_used:
            tools_context.append(f"- {tool}")
        
        tools_used_str = "\n".join(tools_context) if tools_context else "No se utilizaron herramientas MCP"
        
        # Crear mensaje para LangChain
        from langchain_core.messages import SystemMessage, HumanMessage
        
        system_message = f"""Eres un asistente financiero especializado. Utiliza los datos proporcionados para realizar un análisis detallado y profesional.
        
Herramientas utilizadas:
{tools_used_str}
        
Proporciona un análisis claro, preciso y estructurado. Incluye:
1. Un resumen ejecutivo
2. Análisis de puntos clave
3. Métricas relevantes
4. Conclusiones y recomendaciones
"""
        
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=formatted_prompt)
        ]
        
        try:
            # Llamar al LLM con el nuevo método para registrar la conversación
            response = self.invoke_llm(messages, prompt_type="langchain")
            
            if not response or not hasattr(response, 'content'):
                raise ValueError("El LLM no generó una respuesta válida")
                
            result = response.content
            confidence = 0.8  # Nivel de confianza estimado
            
            # Métricas para el resultado
            processing_time = time.time() - start_time
            
            return {
                "result": result,
                "input": query,
                "context": context,
                "data": {
                    "company": company,
                    "industry": industry,
                    "period": period,
                    "financial_data": financial_data
                },
                "confidence": confidence,
                "processing_time": processing_time,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error al generar respuesta financiera: {str(e)}")
            processing_time = time.time() - start_time
            
            return {
                "result": f"Error al procesar la consulta financiera: {str(e)}",
                "input": query,
                "confidence": 0.1,
                "processing_time": processing_time,
                "success": False,
                "error": str(e)
            }
    
    def _format_finance_prompt(self, input_data: Dict[str, Any]) -> str:
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
        services = input_data.get("services", [])
        
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
        {', '.join(services)}
        
        ## Instrucciones:
        1. Analiza detenidamente toda la información financiera proporcionada
        2. Identifica insights financieros relevantes para la consulta
        3. Formula recomendaciones financieras concretas y accionables
        4. Considera aspectos de riesgo, retorno y factores macroeconómicos
        5. Incluye métricas financieras relevantes y su interpretación
        6. Proporciona opciones o escenarios cuando sea apropiado
        
        ## Formato de respuesta:
        Tu análisis debe seguir esta estructura:
        1. Resumen ejecutivo financiero (breve)
        2. Análisis de la situación financiera actual
        3. Recomendaciones estratégicas financieras
        4. Análisis de riesgos y consideraciones importantes
        5. Métricas financieras a monitorear (KPIs)
        6. Próximos pasos recomendados
        
        Responde de manera profesional, basada en datos, y orientada a resultados.
        """
        
        return prompt
        
    def _extract_industry(self, query: str) -> Optional[str]:
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

    def _summarize_financial_data(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
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
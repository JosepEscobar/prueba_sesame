from typing import Dict, Any, List, Optional
import time
import asyncio

from langchain_openai import ChatOpenAI
from app.agents.base import BaseAgent
from app.core.logging import logger
from app.core.config import get_settings
from app.tools.mcp_client import MCPClient

# Obtener la configuración
settings = get_settings()

class FinanceAgent(BaseAgent):
    """
    Agente especializado en análisis financiero y consultoría económica.
    
    Proporciona análisis detallado, recomendaciones y estrategias financieras
    basadas en datos de mercado, indicadores económicos y mejores prácticas
    del sector financiero.
    
    Actualizado para usar herramientas a través del servidor MCP.
    """
    
    def __init__(self):
        """Inicializa el agente de finanzas."""
        super().__init__(
            name="finance_agent",
            description="Especialista en análisis financiero y consultoría económica."
        )
        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)
        self.services = [
            "Análisis financiero",
            "Planificación de presupuestos",
            "Optimización fiscal",
            "Estrategias de inversión",
            "Gestión de riesgos financieros",
            "Valuación empresarial",
            "Análisis de rentabilidad",
            "Modelos financieros",
            "Planificación de flujo de caja"
        ]
        
        # Inicializar el cliente MCP para herramientas externas
        self.mcp_client = MCPClient(
            base_url=settings.MCP_CLIENT_URL
        )
        
        logger.info(f"Agente {self.name} inicializado con {len(self.services)} servicios")
        
    def _execute_impl(self, input_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Implementa la lógica de ejecución del agente financiero.
        
        Args:
            input_data: Datos de entrada que contienen la consulta financiera y contexto
            
        Returns:
            Diccionario con el resultado del análisis financiero, input original y nivel de confianza
        """
        start_time = time.time()
        query = input_data.get("query", "")
        context = input_data.get("context", {})
        
        logger.info(f"Procesando consulta financiera: {query[:50]}...")
        
        # Recopilar datos financieros relevantes utilizando MCP
        financial_data = {}
        
        try:
            # Inicializar cliente MCP si no se ha hecho ya
            loop = asyncio.get_event_loop()
            if not loop.run_until_complete(self.mcp_client.initialize()):
                logger.error("No se pudo inicializar el cliente MCP")
                return {
                    "result": "Error al conectar con el servidor de herramientas externas",
                    "input": query,
                    "confidence": 0.0,
                    "error": "Error de conexión MCP"
                }
            
            logger.info("Utilizando herramientas MCP para enriquecer el análisis financiero")
            
            # Si hay empresas mencionadas, buscar información sobre ellas
            if "company" in context:
                company_data_result = loop.run_until_complete(
                    self.mcp_client.call_tool("data_lookup", {
                        "lookup_type": "company",
                        "query": query,
                        "company": context["company"]
                    })
                )
                if "error" not in company_data_result:
                    financial_data["company_info"] = company_data_result
            
            # Buscar datos de mercado relevantes
            market_data_result = loop.run_until_complete(
                self.mcp_client.call_tool("data_lookup", {
                    "lookup_type": "market_data",
                    "query": query
                })
            )
            if "error" not in market_data_result:
                financial_data["market_data"] = market_data_result
            
            # Buscar noticias financieras recientes
            news_data_result = loop.run_until_complete(
                self.mcp_client.call_tool("data_lookup", {
                    "lookup_type": "news",
                    "query": query + " finanzas"
                })
            )
            if "error" not in news_data_result:
                financial_data["recent_news"] = news_data_result
            
            # Si hay una industria específica, buscar informes del sector
            if "industry" in context:
                industry_report_result = loop.run_until_complete(
                    self.mcp_client.call_tool("data_lookup", {
                        "lookup_type": "industry",
                        "query": query,
                        "industry": context["industry"]
                    })
                )
                if "error" not in industry_report_result:
                    financial_data["industry_reports"] = industry_report_result
            
            # Buscar información web adicional
            web_data_result = loop.run_until_complete(
                self.mcp_client.call_tool("data_lookup", {
                    "lookup_type": "web",
                    "query": query + " análisis financiero"
                })
            )
            if "error" not in web_data_result:
                financial_data["web_resources"] = web_data_result
            
            # Buscar modelos financieros relevantes
            financial_models_result = loop.run_until_complete(
                self.mcp_client.call_tool("financial_models", {
                    "model_type": "forecast",
                    "industry": context.get("industry", "general")
                })
            )
            if "error" not in financial_models_result:
                financial_data["financial_models"] = financial_models_result
            
        except Exception as e:
            logger.error(f"Error al recopilar datos financieros vía MCP: {str(e)}")
            # Continuar con los datos que se hayan podido recopilar
        
        # Preparar input para el prompt con todos los datos recopilados
        prompt_input = {
            "query": query,
            "context": context,
            "financial_data": financial_data,
            "services": self.services
        }
        
        # Formatear el prompt usando el método de formato
        formatted_prompt = self._format_finance_prompt(prompt_input)
        
        # Generar análisis financiero utilizando el LLM
        logger.info("Generando análisis financiero con el LLM")
        response = self.llm.invoke(formatted_prompt)
        
        # Estructurar la respuesta
        processing_time = time.time() - start_time
        
        # Recopilar fuentes de datos utilizadas
        data_sources = []
        for data_type, data in financial_data.items():
            if isinstance(data, dict) and "source" in data:
                data_sources.append({"type": data_type, "source": data["source"]})
        
        result = {
            "result": response.content,
            "data_sources": data_sources,
            "input": input_data.get("query", ""),
            "confidence": 0.89,  # Nivel de confianza alto para respuestas financieras
            "processing_time": processing_time,
            "model": "gpt-3.5-turbo"
        }
        
        logger.info(f"Análisis financiero completado en {processing_time:.2f} segundos")
        
        return result
    
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
        Eres un experto en finanzas y consultoría económica actuando como parte de un sistema 
        de asistencia empresarial. Debes proporcionar un análisis financiero detallado y 
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
        2. Identifica los puntos clave y patrones significativos en los datos
        3. Formula recomendaciones financieras concretas y accionables
        4. Presenta proyecciones o escenarios cuando sea relevante
        5. Incluye consideraciones de riesgo y cómo mitigarlos
        6. Usa terminología financiera precisa pero explica los conceptos complejos
        
        ## Formato de respuesta:
        Tu análisis debe seguir esta estructura:
        1. Resumen ejecutivo del análisis financiero (breve)
        2. Hallazgos clave basados en los datos proporcionados
        3. Recomendaciones estratégicas y tácticas
        4. Métricas o KPIs a monitorear
        5. Próximos pasos recomendados
        
        Responde de manera profesional, basada en datos, y orientada a resultados.
        """
        
        return prompt 
    
    async def get_financial_data(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene datos financieros usando el cliente MCP.
        
        Args:
            query: Consulta del usuario
            context: Contexto adicional
            
        Returns:
            Datos financieros recopilados
        """
        financial_data = {}
        
        try:
            # Inicializar el cliente si no se ha hecho
            if not await self.mcp_client.initialize():
                logger.warning("No se pudo inicializar el cliente MCP")
                return {"error": "No se pudo conectar al servidor MCP"}
            
            # Buscar datos de mercado
            market_data = await self.mcp_client.call_tool("data_lookup", {
                "lookup_type": "market_data",
                "query": query
            })
            if "error" not in market_data:
                financial_data["market_data"] = market_data
            
            # Buscar noticias financieras
            news_data = await self.mcp_client.call_tool("data_lookup", {
                "lookup_type": "news",
                "query": query + " finanzas"
            })
            if "error" not in news_data:
                financial_data["news"] = news_data
            
            # Si hay una industria en el contexto, buscar informes
            if "industry" in context:
                industry_data = await self.mcp_client.call_tool("data_lookup", {
                    "lookup_type": "industry",
                    "industry": context["industry"]
                })
                if "error" not in industry_data:
                    financial_data["industry"] = industry_data
            
            # Si hay una empresa en el contexto, buscar información
            if "company" in context:
                company_data = await self.mcp_client.call_tool("data_lookup", {
                    "lookup_type": "company",
                    "company": context["company"]
                })
                if "error" not in company_data:
                    financial_data["company"] = company_data
            
            # Buscar modelos financieros
            model_type = self._determine_model_type(query)
            financial_models = await self.mcp_client.call_tool("financial_models", {
                "model_type": model_type,
                "industry": context.get("industry", "general")
            })
            if "error" not in financial_models:
                financial_data["models"] = financial_models
            
            return financial_data
            
        except Exception as e:
            logger.error(f"Error al obtener datos financieros: {str(e)}")
            return {"error": str(e)}
    
    def _determine_model_type(self, query: str) -> str:
        """
        Determina el tipo de modelo financiero más relevante para la consulta.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Tipo de modelo financiero
        """
        query = query.lower()
        
        if any(word in query for word in ["flujo", "caja", "efectivo", "liquidez"]):
            return "cash_flow"
        elif any(word in query for word in ["valoración", "valuar", "valor"]):
            return "valuation"
        elif any(word in query for word in ["presupuesto", "gastos"]):
            return "budget"
        elif any(word in query for word in ["proyección", "proyectar", "tendencia", "prever"]):
            return "forecast"
        elif any(word in query for word in ["inversión", "invertir", "capital"]):
            return "investment"
        elif any(word in query for word in ["precio", "tarifa", "estrategia"]):
            return "pricing"
        elif any(word in query for word in ["equilibrio", "breakeven"]):
            return "breakeven"
        elif any(word in query for word in ["retorno", "roi", "rendimiento"]):
            return "roi"
        else:
            # Tipo por defecto
            return "forecast" 
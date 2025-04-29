from typing import Dict, Any, List, Optional
import time

from langchain.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.core.logging import logger
from app.core.config import get_settings
from app.tools.mcp_client import MCPClient
from app.services.data_lookup import DataLookupService

# Obtener la configuración
settings = get_settings()

class DataLookupAgent(BaseAgent):
    """
    Agente especializado en buscar y obtener información de fuentes externas.
    
    Este agente se encarga de realizar búsquedas en diversas fuentes de datos como
    noticias, informes de mercado, información de empresas y contenido web para
    proporcionar información relevante y actualizada para consultas empresariales.
    """
    
    def __init__(self):
        """Inicializa el DataLookupAgent con el servicio de búsqueda de datos."""
        super().__init__(
            name="Data Lookup Agent",
            description="Agente especializado en buscar y obtener información de fuentes externas"
        )
        self.data_service = DataLookupService()
        logger.info(f"DataLookupAgent inicializado con modelo: {settings.OPENAI_MODEL}")
        
        # Inicializar el cliente MCP para herramientas externas
        self.mcp_client = MCPClient(
            base_url=settings.MCP_CLIENT_URL
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un agente especializado en buscar, filtrar y sintetizar información relevante de fuentes externas.
            
            Tu objetivo es encontrar datos precisos y relevantes que puedan complementar las respuestas de otros agentes. Cuando el usuario necesite información específica o actualizada, tu trabajo es:
            
            1. Entender exactamente qué información se necesita buscar
            2. Determinar las mejores fuentes para esa información
            3. Formular consultas efectivas para obtener resultados relevantes
            4. Sintetizar y estructurar la información encontrada
            
            Utilizarás las siguientes herramientas especializadas:
            - search_articles: Busca artículos relevantes sobre un tema
            - query_kb: Consulta la base de conocimiento interna
            - financial_models: Obtiene modelos y plantillas financieras
            
            Proporciona respuestas objetivas y basadas en hechos, citando siempre tus fuentes.
            
            Sigue este formato para tus respuestas:
            
            1. CONSULTA INTERPRETADA: Reformula lo que entendiste que se necesita buscar
            2. FUENTES CONSULTADAS: Lista las fuentes que has utilizado
            3. INFORMACIÓN RELEVANTE: Presenta la información encontrada de forma estructurada
            4. SÍNTESIS: Resume los puntos clave en 2-3 frases
            5. FUENTES: Proporciona referencias
            """),
            ("human", "{query}\n\nContexto de búsqueda: {context}")
        ])
        
    def _execute_impl(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la operación de búsqueda de datos basada en los datos de entrada.
        
        Args:
            input_data: Diccionario que contiene la consulta y cualquier contexto adicional.
                Debe incluir 'query' y opcionalmente 'lookup_type' y 'parameters'.
                
        Returns:
            Dict con los resultados de la búsqueda, la consulta original y un nivel de confianza.
        """
        start_time = time.time()
        
        # Extraer la consulta y parámetros
        query = input_data.get("query", "")
        lookup_type = input_data.get("lookup_type", "general")
        parameters = input_data.get("parameters", {})
        
        logger.info(
            f"DataLookupAgent ejecutando búsqueda",
            extra={
                "agent_name": self.name,
                "lookup_type": lookup_type,
                "query": query[:100] + "..." if len(query) > 100 else query
            }
        )
        
        # Realizar búsqueda según el tipo solicitado
        results = {}
        data_sources = []
        
        try:
            if lookup_type == "market_data" or lookup_type == "general":
                market_data = self.data_service.search_market_data(query)
                results["market_data"] = market_data
                data_sources.append({"type": "market_data", "source": "Alpha Vantage API"})
                
            if lookup_type == "news" or lookup_type == "general":
                news_data = self.data_service.search_news(query)
                results["news"] = news_data
                data_sources.append({"type": "news", "source": "News API"})
                
            if lookup_type == "industry" or lookup_type == "general":
                industry = parameters.get("industry", "")
                if industry:
                    industry_data = self.data_service.search_industry_reports(industry)
                    results["industry"] = industry_data
                    data_sources.append({"type": "industry", "source": "Industry Reports Database"})
                
            if lookup_type == "web" or lookup_type == "general":
                web_data = self.data_service.search_web(query)
                results["web"] = web_data
                data_sources.append({"type": "web", "source": "Bing Search API"})
                
            if lookup_type == "company":
                company = parameters.get("company", "")
                if company:
                    company_data = self.data_service.lookup_company_data(company)
                    results["company"] = company_data
                    data_sources.append({"type": "company", "source": "Company Database"})
            
            # Preparar el prompt para sintetizar los resultados
            prompt = self._prepare_synthesis_prompt(query, results, lookup_type)
            
            # Invocar el LLM para obtener la síntesis
            synthesis = self._invoke_llm(prompt)
            
            processing_time = time.time() - start_time
            
            return {
                "results": results,
                "synthesis": synthesis,
                "data_sources": data_sources,
                "query": query,
                "confidence": 0.85,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(
                f"Error en DataLookupAgent: {str(e)}",
                extra={"agent_name": self.name, "error": str(e)}
            )
            return {
                "results": {},
                "synthesis": f"Error al buscar información: {str(e)}",
                "data_sources": [],
                "query": query,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _prepare_synthesis_prompt(self, query: str, results: Dict[str, Any], lookup_type: str) -> str:
        """
        Prepara el prompt para la síntesis de los resultados de búsqueda.
        
        Args:
            query: La consulta original
            results: Los resultados de la búsqueda
            lookup_type: El tipo de búsqueda realizada
            
        Returns:
            El prompt para el LLM
        """
        # Formatear los resultados para el prompt
        formatted_results = ""
        for result_type, data in results.items():
            formatted_results += f"\n--- {result_type.upper()} ---\n"
            formatted_results += str(data)[:1500]  # Limitar tamaño para no exceder contexto
            formatted_results += "\n"
        
        prompt = f"""
        Eres un especialista en sintetizar y organizar información de múltiples fuentes de datos.
        
        CONSULTA: {query}
        TIPO DE BÚSQUEDA: {lookup_type}
        
        RESULTADOS ENCONTRADOS:
        {formatted_results}
        
        Por favor, sintetiza estos resultados en un formato claro y estructurado siguiendo estas pautas:
        
        1. RESUMEN EJECUTIVO: Una síntesis concisa de los hallazgos principales (2-3 frases)
        2. DATOS CLAVE: Lista de 3-5 puntos con la información más relevante
        3. ANÁLISIS: Breve análisis de cómo esta información responde a la consulta original
        4. RECOMENDACIONES: Si aplica, sugerencias basadas en los datos encontrados
        
        La síntesis debe ser objetiva, basada en hechos y directamente relevante para la consulta original.
        Usa un tono profesional y claro, adecuado para consultoría empresarial.
        """
        
        return prompt
    
    async def _search_external_information(self, query: str) -> Dict[str, Any]:
        """
        Busca información externa usando herramientas MCP.
        
        Args:
            query: Consulta para buscar información
            
        Returns:
            Resultados de la búsqueda
        """
        try:
            # Inicializar el cliente si aún no se ha hecho
            if not await self.mcp_client.initialize():
                logger.warning("No se pudo inicializar el cliente MCP, usando respuesta simulada")
                return {"error": "No se pudo conectar al servidor MCP"}
            
            # Buscar artículos relacionados
            articles_result = await self.mcp_client.call_tool(
                "search_articles", 
                {"query": query, "max_results": 3}
            )
            
            # Consultar la base de conocimiento
            kb_result = await self.mcp_client.call_tool(
                "query_kb", 
                {"query": query, "kb_name": "general"}
            )
            
            # Combinar resultados
            return {
                "articles": articles_result.get("articles", []),
                "kb_results": kb_result.get("results", [])
            }
            
        except Exception as e:
            logger.error(f"Error al buscar información externa: {str(e)}")
            return {"error": str(e)}
            
    def _invoke_llm(self, prompt: str) -> str:
        """
        Invoca el LLM para generar una respuesta basada en el prompt dado.
        
        Args:
            prompt: El prompt para el LLM
            
        Returns:
            La respuesta generada por el LLM
        """
        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"Error al invocar LLM: {str(e)}")
            return f"Error al generar síntesis: {str(e)}" 
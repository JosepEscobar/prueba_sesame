from typing import Dict, Any, List, Optional
import time
import asyncio

from langchain.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.core.logging import logger
from app.core.config import get_settings
from app.tools.mcp_client import MCPClient

# Obtener la configuración
settings = get_settings()

class DataLookupAgent(BaseAgent):
    """
    Agente especializado en buscar y obtener información de fuentes externas.
    
    Este agente se encarga de realizar búsquedas en diversas fuentes de datos como
    noticias, informes de mercado, información de empresas y contenido web para
    proporcionar información relevante y actualizada para consultas empresariales.
    
    Actualizado para usar herramientas a través del servidor MCP.
    """
    
    def __init__(self):
        """Inicializa el DataLookupAgent con el cliente MCP."""
        super().__init__(
            name="Data Lookup Agent",
            description="Agente especializado en buscar y obtener información de fuentes externas"
        )
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
            - data_lookup: Busca información en diferentes fuentes externas
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
        
        # Realizar búsqueda a través del servidor MCP
        results = {}
        data_sources = []
        
        try:
            # Inicializar cliente MCP si no se ha hecho ya
            loop = asyncio.get_event_loop()
            if not loop.run_until_complete(self.mcp_client.initialize()):
                logger.error("No se pudo inicializar el cliente MCP")
                return {
                    "results": {},
                    "synthesis": "Error al conectar con el servidor de herramientas externas",
                    "data_sources": [],
                    "query": query,
                    "confidence": 0.0,
                    "error": "Error de conexión MCP"
                }
            
            # Preparar parámetros para la llamada a data_lookup
            mcp_params = {
                "query": query,
                "lookup_type": lookup_type
            }
            
            # Añadir parámetros adicionales según el tipo de búsqueda
            if lookup_type == "industry" and "industry" in parameters:
                mcp_params["industry"] = parameters["industry"]
                
            if lookup_type == "company" and "company" in parameters:
                mcp_params["company"] = parameters["company"]
            
            # Realizar la llamada a la herramienta data_lookup a través de MCP
            logger.info(f"Llamando a herramienta data_lookup con parámetros: {mcp_params}")
            lookup_result = loop.run_until_complete(
                self.mcp_client.call_tool("data_lookup", mcp_params)
            )
            
            # Procesar resultados
            if "error" in lookup_result:
                logger.error(f"Error en la búsqueda MCP: {lookup_result['error']}")
                return {
                    "results": {},
                    "synthesis": f"Error al buscar información: {lookup_result['error']}",
                    "data_sources": [],
                    "query": query,
                    "confidence": 0.0,
                    "error": lookup_result['error']
                }
            
            # Extraer resultados según el tipo de búsqueda
            if lookup_type == "general":
                # Para búsqueda general, los resultados ya vienen combinados
                results = lookup_result.get("results", {})
                
                # Crear lista de fuentes de datos
                for result_type, data in results.items():
                    if isinstance(data, dict) and "source" in data:
                        data_sources.append({"type": result_type, "source": data["source"]})
            else:
                # Para búsquedas específicas, usar el resultado directamente
                results[lookup_type] = lookup_result
                if "source" in lookup_result:
                    data_sources.append({"type": lookup_type, "source": lookup_result["source"]})
            
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
    
    async def search_with_mcp(self, lookup_type: str, query: str, **params) -> Dict[str, Any]:
        """
        Realiza una búsqueda usando la herramienta data_lookup a través de MCP.
        
        Args:
            lookup_type: Tipo de búsqueda a realizar
            query: Consulta para la búsqueda
            **params: Parámetros adicionales según el tipo de búsqueda
            
        Returns:
            Resultados de la búsqueda
        """
        try:
            # Inicializar el cliente si aún no se ha hecho
            if not await self.mcp_client.initialize():
                logger.warning("No se pudo inicializar el cliente MCP, usando respuesta simulada")
                return {"error": "No se pudo conectar al servidor MCP"}
            
            # Preparar parámetros para la llamada
            mcp_params = {
                "lookup_type": lookup_type,
                "query": query,
                **params
            }
            
            # Realizar la llamada a la herramienta
            result = await self.mcp_client.call_tool("data_lookup", mcp_params)
            return result
            
        except Exception as e:
            logger.error(f"Error al buscar con MCP: {str(e)}")
            return {"error": str(e)}
    
    async def get_financial_models(self, model_type: str, industry: str = "general", 
                                  complexity: str = "intermediate") -> Dict[str, Any]:
        """
        Obtiene modelos financieros usando la herramienta financial_models a través de MCP.
        
        Args:
            model_type: Tipo de modelo financiero
            industry: Industria específica
            complexity: Nivel de complejidad
            
        Returns:
            Modelos financieros disponibles
        """
        try:
            # Inicializar el cliente si aún no se ha hecho
            if not await self.mcp_client.initialize():
                logger.warning("No se pudo inicializar el cliente MCP, usando respuesta simulada")
                return {"error": "No se pudo conectar al servidor MCP"}
            
            # Preparar parámetros para la llamada
            params = {
                "model_type": model_type,
                "industry": industry,
                "complexity": complexity
            }
            
            # Realizar la llamada a la herramienta
            result = await self.mcp_client.call_tool("financial_models", params)
            return result
            
        except Exception as e:
            logger.error(f"Error al obtener modelos financieros: {str(e)}")
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
            return f"Error al procesar la información: {str(e)}" 
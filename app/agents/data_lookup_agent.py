from typing import Dict, Any, List
from langchain.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.core.logging import logger
from app.tools.mcp_client import MCPClient

class DataLookupAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Data Lookup Agent",
            description="Agente especializado en buscar y obtener información de fuentes externas"
        )
        
        # Inicializar el cliente MCP para herramientas externas
        self.mcp_client = MCPClient()
        
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
        
    async def _execute_impl(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la búsqueda de información."""
        try:
            # Preparar el input para el prompt
            query = input_data.get("query", "")
            context = input_data.get("context", "No hay contexto adicional para la búsqueda")
            
            # Simulación de búsqueda de información externa usando herramientas MCP
            search_results = await self._search_external_information(query)
            
            # Añadir los resultados al contexto
            enhanced_context = f"{context}\n\nResultados de búsqueda:\n{search_results}"
            
            prompt_input = {
                "query": query,
                "context": enhanced_context
            }
            
            logger.info(
                f"DataLookupAgent procesando consulta",
                extra={
                    "agent_name": self.name,
                    "query": query[:100] + "..." if len(query) > 100 else query
                }
            )
            
            # Obtener la respuesta del LLM
            chain = self.prompt | self.llm
            response = await chain.ainvoke(prompt_input)
            
            logger.info(
                f"DataLookupAgent generó respuesta",
                extra={
                    "agent_name": self.name,
                    "response_length": len(response.content)
                }
            )
            
            return {
                "data_lookup_result": response.content,
                "search_results": search_results,
                "original_input": input_data,
                "confidence": 0.88
            }
            
        except Exception as e:
            logger.error(
                f"Error en DataLookupAgent: {str(e)}",
                extra={
                    "agent_name": self.name,
                    "error": str(e)
                }
            )
            raise
    
    async def _search_external_information(self, query: str) -> str:
        """
        Simula la búsqueda de información externa usando herramientas MCP.
        En un caso real, aquí se llamaría a las herramientas MCP para obtener información.
        """
        try:
            # Intentamos usar el cliente MCP para buscar artículos
            # En este momento, solo simulamos la búsqueda para demostración
            logger.info(
                f"Buscando información externa para: {query}",
                extra={"agent_name": self.name, "query": query}
            )
            
            # Simulación de datos encontrados (en una implementación real, esto vendría de las herramientas MCP)
            # Para áreas de consultoría empresarial
            if "marketing" in query.lower():
                return """
                1. Artículo: "Tendencias de Marketing Digital 2023" - Harvard Business Review
                   - Resumen: El artículo destaca el aumento del marketing de contenido, la personalización y el uso de IA en estrategias de marketing.
                   - Fecha: Marzo 2023
                   - URL: https://hbr.org/marketing/trends2023
                
                2. Informe: "Efectividad de Campañas en Redes Sociales" - Marketing Institute
                   - Datos clave: Las campañas en Instagram tienen un ROI promedio 23% mayor que Facebook para productos B2C.
                   - Fecha: Enero 2023
                   - URL: https://marketinginstitute.com/reports/social2023
                """
            elif "finanzas" in query.lower() or "financiero" in query.lower():
                return """
                1. Artículo: "Estrategias de Inversión para Startups" - Financial Times
                   - Resumen: Análisis de rondas de financiación, valoraciones y estrategias de exit para 2023.
                   - Fecha: Abril 2023
                   - URL: https://ft.com/startups/investment2023
                
                2. Modelo financiero: "Plantilla de Proyección Financiera para SaaS"
                   - Detalles: Modelo en Excel con proyecciones a 5 años, cálculos de CAC, LTV y punto de equilibrio.
                   - Autor: McKinsey & Company
                   - URL: https://resources.mckinsey.com/financial-models/saas2023
                """
            elif "operaciones" in query.lower() or "procesos" in query.lower():
                return """
                1. Estudio: "Optimización de Cadena de Suministro Post-Pandemia" - MIT Supply Chain Review
                   - Resumen: Nuevas prácticas de resiliencia en cadenas de suministro, automatización y gestión de inventario.
                   - Fecha: Febrero 2023
                   - URL: https://mitscr.edu/studies/supply-chain-resilience
                
                2. Guía: "Implementación de Lean Management en Empresas Medianas"
                   - Puntos clave: Metodología paso a paso, casos de estudio y métricas de seguimiento.
                   - Autor: Toyota Production System Institute
                   - URL: https://tpsi.org/resources/lean-medium-business
                """
            else:
                return """
                1. Artículo: "Tendencias Empresariales 2023" - Business Insider
                   - Resumen: Análisis de tendencias en digitalización, sostenibilidad y modelos de trabajo híbridos.
                   - Fecha: Enero 2023
                   - URL: https://businessinsider.com/trends2023
                
                2. Informe: "Estado de la Consultoría Empresarial" - Deloitte
                   - Datos clave: Sectores de mayor crecimiento, tarifas promedio y especialidades emergentes.
                   - Fecha: Marzo 2023
                   - URL: https://deloitte.com/insights/consulting-state
                """
            
        except Exception as e:
            logger.error(
                f"Error buscando información externa: {str(e)}",
                extra={"agent_name": self.name, "error": str(e)}
            )
            return "No se pudo obtener información externa debido a un error." 
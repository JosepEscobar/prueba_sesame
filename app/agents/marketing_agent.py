from typing import Any, Dict, Optional
import time
import json

from langchain_openai import ChatOpenAI 
from app.agents.base import BaseAgent
from app.core.logging import logger
from app.core.metrics import MetricsCollector


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
        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.3)
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
        logger.info(f"Agente {self.name} inicializado con {len(self.services)} servicios")

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
        
        logger.info(f"Procesando consulta de marketing: {query[:50]}...")
        
        # Recopilar datos de marketing relevantes
        marketing_data = {}
        data_service = self.get_tool("data_lookup")
        
        if data_service:
            logger.info("Utilizando servicio de búsqueda de datos para enriquecer el análisis de marketing")
            
            # Buscar noticias de marketing y tendencias recientes
            news_data = data_service.search_news(query + " marketing tendencias")
            marketing_data["recent_news"] = news_data
            
            # Si hay una industria específica, buscar informes del sector
            if "industry" in context:
                industry_reports = data_service.search_industry_reports(context["industry"])
                marketing_data["industry_reports"] = industry_reports
            
            # Si hay un mercado objetivo específico, buscar datos demográficos
            if "target_market" in context:
                market_data = data_service.search_market_data(f"demografía {context['target_market']}")
                marketing_data["market_demographics"] = market_data
            
            # Buscar información web adicional sobre marketing digital
            web_data = data_service.search_web(query + " marketing digital estrategias")
            marketing_data["web_resources"] = web_data
            
            # Si se mencionan competidores, buscar información sobre ellos
            if "competitors" in context and isinstance(context["competitors"], list):
                competitors_data = {}
                for competitor in context["competitors"]:
                    competitor_info = data_service.lookup_company_data(competitor)
                    competitors_data[competitor] = competitor_info
                marketing_data["competitors_info"] = competitors_data
        else:
            logger.warning("Servicio de búsqueda de datos no disponible para el agente de marketing")
        
        # Preparar input para el prompt con todos los datos recopilados
        prompt_input = {
            "query": query,
            "context": context,
            "marketing_data": marketing_data,
            "services": self.services
        }
        
        # Generar análisis de marketing utilizando el LLM
        logger.info("Generando análisis de marketing con el LLM")
        response = self.llm.invoke(
            self._format_marketing_prompt(prompt_input)
        )
        
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
            "result": response.content,
            "data_sources": data_sources,
            "input": input_data.get("query", ""),
            "confidence": 0.87,  # Nivel de confianza para respuestas de marketing
            "processing_time": processing_time,
            "model": "gpt-3.5-turbo"
        }
        
        logger.info(f"Análisis de marketing completado en {processing_time:.2f} segundos")
        
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
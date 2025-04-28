from typing import Dict, Any, List, Optional
import time

from app.agents.base import BaseAgent
from app.core.logging import logger
from app.services.data_lookup import DataLookupService


class FinanceAgent(BaseAgent):
    """
    Agente especializado en análisis financiero y consultoría económica.
    
    Proporciona análisis detallado, recomendaciones y estrategias financieras
    basadas en datos de mercado, indicadores económicos y mejores prácticas
    del sector financiero.
    """
    
    def __init__(self):
        """Inicializa el agente de finanzas."""
        super().__init__(
            name="finance_agent",
            description="Especialista en análisis financiero y consultoría económica."
        )
        self.data_service = DataLookupService()
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
        logger.info(f"Agente {self.name} inicializado con {len(self.services)} servicios")
        
    def _execute_impl(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
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
        
        logger.info(f"Procesando consulta financiera: {query}")
        
        # Recopilar datos financieros relevantes
        financial_data = {}
        
        # Si hay empresas mencionadas, buscar información sobre ellas
        if "company" in context:
            company_data = self.data_service.lookup_company_data(context["company"])
            financial_data["company_info"] = company_data
            
        # Buscar datos de mercado relevantes
        market_data = self.data_service.search_market_data(query)
        financial_data["market_data"] = market_data
        
        # Buscar noticias financieras recientes
        news_data = self.data_service.search_news(query + " finanzas")
        financial_data["recent_news"] = news_data
        
        # Si hay una industria específica, buscar informes del sector
        if "industry" in context:
            industry_reports = self.data_service.search_industry_reports(context["industry"])
            financial_data["industry_reports"] = industry_reports
        
        # Preparar input para el prompt con todos los datos recopilados
        prompt_input = {
            "query": query,
            "context": context,
            "financial_data": financial_data,
            "services": self.services
        }
        
        # Generar análisis financiero utilizando el LLM
        response = self.llm.invoke(
            self._format_finance_prompt(prompt_input)
        )
        
        # Estructurar la respuesta
        result = {
            "analysis": response.content,
            "data_sources": [
                source.get("source", "Unknown") 
                for source in [market_data, news_data] 
                if "source" in source
            ],
            "input": input_data,
            "confidence": 0.89  # Nivel de confianza alto para respuestas financieras
        }
        
        logger.info(f"Análisis financiero completado en {time.time() - start_time:.2f} segundos")
        
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
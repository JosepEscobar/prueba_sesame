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
from app.agents.mcp_integration import configure_agent_with_mcp, get_mcp_tools_sync

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
    
    def _execute_impl(self, input_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Ejecuta el análisis financiero.
        """
        start_time = time.time()
        
        try:
            # Extraer la consulta
            query = input_data.get("query", "")
            context = input_data.get("context", {})
            
            # Loguear la consulta con un límite seguro
            query_preview = query[:50] + "..." if len(query) > 50 else query
            logger.info(f"FinanceAgent procesando consulta: {query_preview}")
            
            # Si no hay un LLM configurado (por falta de API key), generar una respuesta simulada
            if self.llm is None:
                logger.warning("No hay clave API de OpenAI válida. Generando respuesta simulada.")
                
                # Extraer la industria si está disponible
                industry = context.get("industry", "")
                if not industry:
                    industry = self._extract_industry(query)
                    
                # Generar un modelo financiero simulado para la industria específica
                financial_model = self._generate_fallback_model(industry)
                
                processing_time = time.time() - start_time
                return {
                    "result": {
                        "content": financial_model,
                        "source": "finance_agent",
                        "model_type": "fallback",
                        "industry": industry
                    },
                    "confidence": 0.7,
                    "processing_time": processing_time,
                    "reasoning": "Generado con modo fallback - sin OpenAI API"
                }
            
            # Construir el prompt para el análisis financiero
            prompt = self._format_finance_prompt(input_data)
            
            # Llamar al LLM para generar el análisis
            response = self.invoke_llm(prompt)
            
            # Procesar la respuesta
            processing_time = time.time() - start_time
            
            # Retornar el resultado completo, no solo un mensaje genérico
            return {
                "result": {
                    "content": response,
                    "source": "finance_agent",
                    "model_type": "openai",
                    "query": query
                },
                "input": input_data,
                "confidence": 0.9,
                "processing_time": processing_time,
                "reasoning": "Clasificado por análisis de la consulta"
            }
            
        except Exception as e:
            logger.error(f"Error en FinanceAgent: {str(e)}")
            
            # En caso de error, generar una respuesta fallback
            industry = input_data.get("context", {}).get("industry", "tecnología")
            financial_model = self._generate_fallback_model(industry)
            
            processing_time = time.time() - start_time
            return {
                "result": {
                    "content": financial_model,
                    "source": "finance_agent",
                    "model_type": "fallback_error",
                    "error": str(e)
                },
                "confidence": 0.5,
                "processing_time": processing_time,
                "reasoning": f"Generado con modo fallback debido a error: {str(e)}"
            }

    def _generate_fallback_model(self, industry: str) -> str:
        """
        Genera un modelo financiero básico cuando el LLM no está disponible.
        
        Args:
            industry: La industria para la que se genera el modelo
            
        Returns:
            Un modelo financiero textual básico
        """
        industry = industry.lower() if industry else "tecnología"
        
        if "tecnolog" in industry:
            return """# Modelo Financiero para el Sector Tecnológico con Proyección de Crecimiento

## 1. Resumen Ejecutivo
Este modelo financiero proporciona proyecciones de crecimiento para empresas en el sector tecnológico, con un enfoque en SaaS, hardware y servicios cloud. Las proyecciones estiman un crecimiento anual del 15-20% durante los próximos 5 años.

## 2. Supuestos Clave
- Crecimiento de ingresos: 15-20% anual
- Margen bruto: 65-75%
- Gastos operativos: 40-45% de ingresos
- Inversión en I+D: 15-20% de ingresos
- CAPEX: 8-12% de ingresos anuales
- Tasa de impuestos efectiva: 22-25%

## 3. Proyecciones Financieras (5 años)
### Año 1
- Ingresos: Base + 18%
- EBITDA: 28% de ingresos
- Flujo de caja libre: 15% de ingresos

### Año 2
- Ingresos: Año 1 + 19%
- EBITDA: 30% de ingresos
- Flujo de caja libre: 17% de ingresos

### Año 3-5
- Ingresos: CAGR del 20%
- EBITDA: Expansión al 32% 
- Flujo de caja libre: 20% de ingresos

## 4. Métricas Clave de Valoración
- EV/EBITDA: 18-22x
- P/E: 25-30x
- EV/Ingresos: 6-8x

## 5. Factores de Crecimiento
- Adopción continua de soluciones cloud
- Expansión de IA y automatización
- Incremento en ciberseguridad
- Nuevos mercados emergentes

## 6. Riesgos
- Competencia intensificada
- Cambios regulatorios
- Rápida obsolescencia tecnológica
- Volatilidad macroeconómica

Este modelo financiero es indicativo y debe adaptarse a la situación específica de cada empresa dentro del sector tecnológico."""
            
        elif "finanz" in industry or "financ" in industry:
            return """# Modelo Financiero para el Sector Financiero con Proyección de Crecimiento

## 1. Resumen Ejecutivo
Este modelo financiero proyecta el crecimiento para instituciones del sector financiero, incluyendo bancos, aseguradoras y fintechs, con estimaciones de crecimiento del 8-12% anual durante los próximos 5 años.

## 2. Supuestos Clave
- Crecimiento de ingresos: 8-12% anual
- Margen neto de interés: 3.2-3.8%
- Ratio de eficiencia: 50-55%
- Provisiones para préstamos: 0.8-1.2% de la cartera
- ROE objetivo: 12-15%
- Ratio CET1: >12%

## 3. Proyecciones Financieras (5 años)
### Año 1
- Ingresos: Base + 9%
- ROA: 1.1%
- Crecimiento de activos: 7%

### Año 2
- Ingresos: Año 1 + 10%
- ROA: 1.2%
- Crecimiento de activos: 8%

### Año 3-5
- Ingresos: CAGR del 11%
- ROA: Mejora a 1.4%
- Crecimiento de activos: 10% anual

## 4. Métricas Clave de Valoración
- P/B: 1.2-1.5x
- P/E: 10-14x
- Dividend Yield: 3-4%

## 5. Factores de Crecimiento
- Digitalización acelerada
- Nuevos productos fintech
- Expansión internacional
- Gestión de patrimonios

## 6. Riesgos
- Entorno de bajos tipos de interés
- Mayor regulación
- Competencia de nuevas fintechs
- Riesgos cibernéticos

Este modelo financiero es indicativo y debe adaptarse a la situación específica de cada institución financiera."""
        else:
            return f"""# Modelo Financiero para el Sector de {industry.capitalize()} con Proyección de Crecimiento

## 1. Resumen Ejecutivo
Este modelo financiero proporciona proyecciones de crecimiento para empresas en el sector de {industry}, con un enfoque en las tendencias actuales del mercado. Las proyecciones estiman un crecimiento anual del 10-15% durante los próximos 5 años.

## 2. Supuestos Clave
- Crecimiento de ingresos: 10-15% anual
- Margen bruto: 50-60%
- Gastos operativos: 35-40% de ingresos
- Inversión en desarrollo: 10-15% de ingresos
- CAPEX: 5-10% de ingresos anuales
- Tasa de impuestos efectiva: 20-25%

## 3. Proyecciones Financieras (5 años)
### Año 1
- Ingresos: Base + 12%
- EBITDA: 25% de ingresos
- Flujo de caja libre: 12% de ingresos

### Año 2
- Ingresos: Año 1 + 13%
- EBITDA: 26% de ingresos
- Flujo de caja libre: 14% de ingresos

### Año 3-5
- Ingresos: CAGR del 15%
- EBITDA: Expansión al 28% 
- Flujo de caja libre: 16% de ingresos

## 4. Métricas Clave de Valoración
- EV/EBITDA: 12-16x
- P/E: 18-22x
- EV/Ingresos: 3-5x

## 5. Factores de Crecimiento
- Innovación constante
- Expansión a nuevos mercados
- Mejora de eficiencia operativa
- Estrategias de marketing digital

## 6. Riesgos
- Competencia en aumento
- Cambios en preferencias del consumidor
- Presiones regulatorias
- Volatilidad económica

Este modelo financiero es indicativo y debe adaptarse a la situación específica de cada empresa dentro del sector."""

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
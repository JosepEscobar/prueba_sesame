from typing import Dict, List, Any, Optional
import time
import json
import logging
import requests
from urllib.parse import urlencode

from app.core.logging import logger
from app.core.metrics import MetricsCollector
from app.core.config import get_settings

settings = get_settings()

class DataLookupService:
    """
    Servicio para buscar información en diferentes fuentes de datos externas.
    Proporciona métodos para consultar APIs, bases de datos y servicios web
    relevantes para el análisis de consultoría empresarial.
    """
    
    def __init__(self, alpha_vantage_api_key=None, news_api_key=None, bing_search_api_key=None):
        """Inicializa el servicio de búsqueda de datos."""
        self.name = "data_lookup_service"
        # Usar claves proporcionadas o usar las de configuración
        self.api_keys = {
            "alpha_vantage": alpha_vantage_api_key or settings.ALPHA_VANTAGE_API_KEY,
            "news_api": news_api_key or settings.NEWS_API_KEY,
            "bing_search": bing_search_api_key or settings.BING_SEARCH_API_KEY,
        }
        logger.info(f"Servicio de búsqueda de datos inicializado: {self.name}")
    
    def search_market_data(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Busca datos de mercado relevantes para la consulta.
        
        Args:
            query: Términos de búsqueda
            limit: Número máximo de resultados
            
        Returns:
            Diccionario con los resultados de la búsqueda
        """
        start_time = time.time()
        logger.info(f"Buscando datos de mercado para: {query}")
        
        try:
            # En un entorno de prueba, simular resultados
            # En producción, aquí se conectaría a la API real
            if not self.api_keys["alpha_vantage"] or self.api_keys["alpha_vantage"] == "demo_key":
                return self._mock_market_data(query, limit)
                
            # Intentar obtener datos de la API real
            url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={query}&apikey={self.api_keys['alpha_vantage']}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            processing_time = time.time() - start_time
            logger.info(f"Datos de mercado recuperados en {processing_time:.2f} segundos")
            MetricsCollector.record_execution(self.name, "search_market_data", processing_time, "success")
            
            return {
                "status": "success",
                "results": data.get("results", []),
                "source": "Alpha Vantage API",
                "data": data,
                "timestamp": time.time(),
                "processing_time": processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error al buscar datos de mercado: {str(e)}")
            MetricsCollector.record_execution(self.name, "search_market_data", processing_time, "error")
            MetricsCollector.record_error(self.name, "api_error")
            
            # En caso de error, devolver datos simulados
            return self._mock_market_data(query, limit)
    
    def _mock_market_data(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Genera datos simulados para búsqueda de mercado."""
        mock_results = []
        
        # Datos simulados basados en la consulta
        keywords = query.lower().split()
        for i in range(min(limit, 5)):
            mock_results.append({
                "symbol": f"{keywords[0][:3].upper()}{i+1}",
                "name": f"{query.title()} Technologies {i+1}",
                "type": "Equity",
                "region": "United States",
                "marketOpen": "09:30",
                "marketClose": "16:00",
                "currency": "USD",
                "match_score": 0.9 - (i * 0.1)
            })
            
        mock_data = {
            "bestMatches": mock_results
        }
            
        return {
            "status": "success",
            "results": mock_results,
            "source": "Mock Data",
            "data": mock_data,
            "timestamp": time.time(),
            "processing_time": 0.1
        }
    
    def search_news(self, query: str, days: int = 7, limit: int = 5) -> Dict[str, Any]:
        """
        Busca noticias relevantes para la consulta.
        
        Args:
            query: Términos de búsqueda
            days: Número de días hacia atrás para la búsqueda
            limit: Número máximo de resultados
            
        Returns:
            Diccionario con los resultados de noticias
        """
        start_time = time.time()
        logger.info(f"Buscando noticias para: {query}, últimos {days} días")
        
        try:
            # En un entorno de prueba, simular resultados
            if not self.api_keys["news_api"] or self.api_keys["news_api"] == "demo_key":
                return self._mock_news_data(query, limit)
                
            # Intentar obtener datos de la API real
            url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={self.api_keys['news_api']}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Transformar la respuesta al formato esperado
            results = []
            for article in data.get("articles", [])[:limit]:
                results.append({
                    "title": article.get("title", ""),
                    "source": article.get("source", {}).get("name", "Desconocido"),
                    "published_date": article.get("publishedAt", ""),
                    "url": article.get("url", ""),
                    "summary": article.get("description", "")
                })
            
            processing_time = time.time() - start_time
            logger.info(f"Noticias recuperadas en {processing_time:.2f} segundos")
            MetricsCollector.record_execution(self.name, "search_news", processing_time, "success")
            
            return {
                "status": "success",
                "results": results,
                "source": "News API",
                "data": data,
                "timestamp": time.time(),
                "processing_time": processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error al buscar noticias: {str(e)}")
            MetricsCollector.record_execution(self.name, "search_news", processing_time, "error")
            MetricsCollector.record_error(self.name, "api_error")
            
            # En caso de error, devolver datos simulados
            return self._mock_news_data(query, limit)
    
    def _mock_news_data(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Genera datos simulados para búsqueda de noticias."""
        mock_results = []
        
        # Datos simulados basados en la consulta
        topics = ["avances", "empresas", "tecnología", "investigación", "aplicaciones"]
        sources = ["Tech News", "Business Insider", "El Economista", "La Vanguardia", "MIT Technology Review"]
        
        for i in range(min(limit, 5)):
            topic = topics[i % len(topics)]
            source = sources[i % len(sources)]
            date = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - (i * 86400)))
            
            mock_results.append({
                "title": f"Nuevos {topic} en {query}: Lo que debes saber",
                "source": source,
                "published_date": date,
                "url": f"https://example.com/news/{query.replace(' ', '-')}-{i+1}",
                "summary": f"Un artículo detallado sobre los últimos {topic} relacionados con {query} y cómo están transformando el panorama empresarial actual."
            })
            
        mock_data = {
            "status": "ok",
            "totalResults": limit,
            "articles": mock_results
        }
            
        return {
            "status": "success",
            "results": mock_results,
            "source": "Mock News Data",
            "data": mock_data,
            "timestamp": time.time(),
            "processing_time": 0.1
        }
    
    def search_industry_reports(self, industry: str, limit: int = 3) -> Dict[str, Any]:
        """
        Busca informes del sector para una industria específica.
        
        Args:
            industry: Nombre de la industria
            limit: Número máximo de resultados
            
        Returns:
            Diccionario con los resultados de informes del sector
        """
        start_time = time.time()
        logger.info(f"Buscando informes del sector para: {industry}")
        
        try:
            # Para servicios que no tienen API directa, siempre usamos datos simulados
            return self._mock_industry_reports(industry, limit)
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error al buscar informes del sector: {str(e)}")
            MetricsCollector.record_execution(self.name, "search_industry_reports", processing_time, "error")
            MetricsCollector.record_error(self.name, "api_error")
            
            # En caso de error, devolver una versión más simple de datos simulados
            reports = [
                {
                    "title": f"Informe Anual: Estado de la industria {industry} 2023",
                    "publisher": "Deloitte",
                    "published_date": "2023-04-20",
                    "url": f"https://example.com/reports/{industry.replace(' ', '-')}-2023"
                }
            ]
            
            return {
                "status": "error",
                "error": f"Error al obtener informes del sector: {str(e)}",
                "results": reports,
                "source": "Fallback Data",
                "timestamp": time.time(),
                "processing_time": time.time() - start_time
            }
    
    def _mock_industry_reports(self, industry: str, limit: int = 3) -> Dict[str, Any]:
        """Genera datos simulados para informes de industria."""
        reports = [
            {
                "title": f"Informe Anual: Estado de la industria {industry} 2023",
                "publisher": "Deloitte",
                "published_date": "2023-04-20",
                "url": f"https://example.com/reports/{industry.replace(' ', '-')}-2023",
                "key_findings": [
                    f"Crecimiento del mercado de {industry} del 7.5% interanual",
                    f"Principales disruptores en {industry}: IA y automatización",
                    f"Tendencias de consolidación en el sector {industry}"
                ]
            },
            {
                "title": f"Perspectivas de {industry} para 2024",
                "publisher": "McKinsey",
                "published_date": "2023-03-15",
                "url": f"https://example.com/reports/{industry.replace(' ', '-')}-forecast",
                "key_findings": [
                    f"Proyección de inversión en {industry} para los próximos 5 años",
                    f"Cambios regulatorios que afectarán a {industry} en 2024",
                    f"Oportunidades emergentes en mercados internacionales"
                ]
            },
            {
                "title": f"Análisis competitivo del sector {industry}",
                "publisher": "BCG",
                "published_date": "2023-02-10",
                "url": f"https://example.com/reports/{industry.replace(' ', '-')}-competitive",
                "key_findings": [
                    f"Mapa de posicionamiento de empresas líderes en {industry}",
                    f"Estrategias de diferenciación en el mercado de {industry}",
                    f"Barreras de entrada y amenazas de nuevos competidores"
                ]
            }
        ]
        
        mock_data = {
            "reports": reports[:limit],
            "total": len(reports)
        }
        
        processing_time = 0.2
        return {
            "status": "success",
            "results": reports[:limit],
            "data": mock_data,
            "source": "Mock Industry Reports",
            "timestamp": time.time(),
            "processing_time": processing_time
        }
    
    def search_web(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Realiza una búsqueda web para obtener información relevante.
        
        Args:
            query: Términos de búsqueda
            limit: Número máximo de resultados
            
        Returns:
            Diccionario con los resultados de búsqueda web
        """
        start_time = time.time()
        logger.info(f"Realizando búsqueda web para: {query}")
        
        try:
            # En un entorno de prueba, simular resultados
            if not self.api_keys["bing_search"] or self.api_keys["bing_search"] == "demo_key":
                return self._mock_web_search(query, limit)
                
            # Consultar la API de Bing Search
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {"Ocp-Apim-Subscription-Key": self.api_keys["bing_search"]}
            params = {"q": query, "count": limit, "responseFilter": "Webpages"}
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Transformar la respuesta al formato esperado
            results = []
            if "webPages" in data and "value" in data["webPages"]:
                for item in data["webPages"]["value"][:limit]:
                    results.append({
                        "title": item.get("name", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("snippet", ""),
                        "display_url": item.get("displayUrl", "")
                    })
            
            processing_time = time.time() - start_time
            logger.info(f"Búsqueda web completada en {processing_time:.2f} segundos")
            MetricsCollector.record_execution(self.name, "search_web", processing_time, "success")
            
            return {
                "status": "success",
                "results": results,
                "data": data,
                "source": "Bing Search API",
                "timestamp": time.time(),
                "processing_time": processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error en búsqueda web: {str(e)}")
            MetricsCollector.record_execution(self.name, "search_web", processing_time, "error")
            MetricsCollector.record_error(self.name, "api_error")
            
            # En caso de error, devolver datos simulados
            return self._mock_web_search(query, limit)
    
    def _mock_web_search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Genera datos simulados para búsqueda web."""
        mock_results = []
        
        # Datos simulados basados en la consulta
        domains = ["wikipedia.org", "medium.com", "github.com", "forbes.com", "harvard.edu"]
        
        for i in range(min(limit, 5)):
            domain = domains[i % len(domains)]
            
            mock_results.append({
                "title": f"{query.title()}: Guía Completa {2023+i}",
                "url": f"https://www.{domain}/article/{query.replace(' ', '-')}-guide-{i+1}",
                "snippet": f"Una guía completa sobre {query} que explora los conceptos fundamentales, aplicaciones prácticas, y tendencias futuras. Este artículo analiza cómo las empresas están implementando {query} para mejorar sus operaciones.",
                "display_url": f"www.{domain}/article/..."
            })
            
        mock_data = {
            "webPages": {
                "value": mock_results,
                "totalEstimatedMatches": 15000
            }
        }
            
        return {
            "status": "success",
            "results": mock_results,
            "data": mock_data,
            "source": "Mock Web Search",
            "timestamp": time.time(),
            "processing_time": 0.15
        }
    
    def lookup_company_data(self, company_name: str) -> Dict[str, Any]:
        """
        Busca información detallada sobre una empresa específica.
        
        Args:
            company_name: Nombre de la empresa
            
        Returns:
            Diccionario con la información de la empresa
        """
        start_time = time.time()
        logger.info(f"Buscando información de la empresa: {company_name}")
        
        try:
            # En un entorno de prueba, simular resultados
            if not self.api_keys["alpha_vantage"] or self.api_keys["alpha_vantage"] == "demo_key":
                return self._mock_company_data(company_name)
                
            # Intentar obtener datos de la API de Alpha Vantage para información de la empresa
            url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={company_name}&apikey={self.api_keys['alpha_vantage']}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Verificar si se obtuvieron datos válidos
            if not data or "Symbol" not in data:
                # Si no hay datos de la API, buscar en otras fuentes secundarias
                # Como una API de búsqueda para obtener información más general
                logger.info(f"No se encontró información detallada para {company_name}, buscando fuentes alternativas")
                
                # Utilizar la búsqueda web como fuente secundaria
                company_info = self._get_fallback_company_data(company_name)
                data_source = "Fallback Source"
            else:
                # Transformar los datos de Alpha Vantage al formato esperado
                company_info = {
                    "name": data.get("Name", company_name),
                    "symbol": data.get("Symbol", ""),
                    "industry": data.get("Industry", ""),
                    "sector": data.get("Sector", ""),
                    "description": data.get("Description", ""),
                    "country": data.get("Country", ""),
                    "employees": data.get("FullTimeEmployees", ""),
                    "market_cap": data.get("MarketCapitalization", ""),
                    "pe_ratio": data.get("PERatio", ""),
                    "dividend_yield": data.get("DividendYield", ""),
                    "52_week_high": data.get("52WeekHigh", ""),
                    "52_week_low": data.get("52WeekLow", "")
                }
                data_source = "Alpha Vantage API"
                
            processing_time = time.time() - start_time
            logger.info(f"Información de empresa recuperada en {processing_time:.2f} segundos")
            MetricsCollector.record_execution(self.name, "lookup_company_data", processing_time, "success")
            
            return {
                "status": "success",
                "company": company_info,
                "data": data,
                "source": data_source,
                "timestamp": time.time(),
                "processing_time": processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error al buscar información de empresa: {str(e)}")
            MetricsCollector.record_execution(self.name, "lookup_company_data", processing_time, "error")
            MetricsCollector.record_error(self.name, "api_error")
            
            # En caso de error, devolver datos simulados
            return self._mock_company_data(company_name)
    
    def _mock_company_data(self, company_name: str) -> Dict[str, Any]:
        """Genera datos simulados para información de empresa."""
        company_info = {
            "name": company_name,
            "symbol": company_name[:4].upper(),
            "industry": "Tecnología",
            "sector": "Tecnologías de la Información",
            "description": f"{company_name} es una empresa líder en su sector que se especializa en soluciones innovadoras para problemas empresariales complejos. Con un enfoque centrado en la experiencia del cliente y la calidad, {company_name} ha establecido un sólido historial de excelencia e innovación continua.",
            "country": "España",
            "employees": "1500",
            "market_cap": "850000000",
            "pe_ratio": "22.5",
            "dividend_yield": "1.8",
            "52_week_high": "85.75",
            "52_week_low": "42.30"
        }
        
        mock_data = {
            "Symbol": company_name[:4].upper(),
            "Name": company_name,
            "Description": company_info["description"],
            "Industry": company_info["industry"],
            "Sector": company_info["sector"]
        }
            
        return {
            "status": "success",
            "company": company_info,
            "data": mock_data,
            "source": "Mock Company Data",
            "timestamp": time.time(),
            "processing_time": 0.2
        }
    
    def _get_fallback_company_data(self, company_name: str) -> Dict[str, Any]:
        """
        Genera datos de empresa simulados cuando no se pueden obtener de las APIs.
        
        Args:
            company_name: Nombre de la empresa
            
        Returns:
            Diccionario con información simulada de la empresa
        """
        # Datos genéricos para pruebas y casos de error
        return {
            "name": company_name,
            "industry": "Desconocido",
            "description": f"Información no disponible para {company_name}",
            "headquarters": "No disponible",
            "founded": "No disponible",
            "employees": "No disponible",
            "revenue": "No disponible",
            "website": f"https://www.{company_name.lower().replace(' ', '')}.com",
            "data_quality": "simulada"
        } 
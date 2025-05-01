"""
Implementaciones de herramientas de búsqueda de datos.

Este módulo contiene herramientas para buscar y recuperar
información de diferentes fuentes, incluyendo datos financieros,
de mercado y noticias.
"""

from typing import Dict, Any, List, Optional
import time
import random
import json
import requests
from urllib.parse import urlencode
from datetime import datetime, timedelta

from app.core.logging import logger
from app.core.metrics import MetricsCollector
from app.core.config import get_settings

settings = get_settings()

class DataLookupImplementation:
    """
    Implementación de la herramienta para buscar información en diferentes fuentes externas.
    Adaptada para ser compatible con el servidor MCP.
    """
    
    def __init__(self, alpha_vantage_api_key=None, news_api_key=None, bing_search_api_key=None):
        """Inicializa la implementación con claves de API y configuraciones."""
        self.name = "data_lookup"
        # Usar claves proporcionadas o usar las de configuración
        self.api_keys = {
            "alpha_vantage": alpha_vantage_api_key or settings.ALPHA_VANTAGE_API_KEY,
            "news_api": news_api_key or settings.NEWS_API_KEY,
            "bing_search": bing_search_api_key or settings.BING_SEARCH_API_KEY,
        }
        self.metrics = MetricsCollector()
        logger.info(f"Implementación de búsqueda de datos inicializada: {self.name}")
    
    def search_market_data(self, query: str) -> Dict[str, Any]:
        """
        Busca datos de mercado relevantes para la consulta.
        
        Args:
            query: Consulta sobre datos de mercado
            
        Returns:
            Datos de mercado encontrados
        """
        start_time = time.time()
        
        try:
            logger.info(f"Buscando datos de mercado para: {query[:50]}...")
            
            # Intentar usar Alpha Vantage API si hay clave disponible
            if self.api_keys.get("alpha_vantage"):
                try:
                    # Determinar símbolos relevantes de la consulta
                    symbols = self._extract_market_symbols(query)
                    
                    if symbols:
                        # Obtener datos para cada símbolo
                        results = {}
                        for symbol in symbols[:3]:  # Limitar a 3 símbolos para no exceder límites de API
                            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.api_keys['alpha_vantage']}"
                            response = requests.get(url, timeout=10)
                            
                            if response.status_code == 200:
                                data = response.json()
                                if "Global Quote" in data and data["Global Quote"]:
                                    results[symbol] = data["Global Quote"]
                        
                        if results:
                            execution_time = time.time() - start_time
                            self.metrics.record_lookup_execution(
                                lookup_type="market_data",
                                execution_time=execution_time,
                                status="success"
                            )
                            
                            return {
                                "data": results,
                                "source": "Alpha Vantage API",
                                "timestamp": time.time()
                            }
                    
                except Exception as e:
                    logger.warning(f"Error al obtener datos de Alpha Vantage: {str(e)}")
            
            # Si no hay clave o falló la búsqueda, generar datos simulados
            logger.info("Usando datos de mercado simulados")
            mock_data = self._generate_mock_market_data(query)
            
            execution_time = time.time() - start_time
            self.metrics.record_lookup_execution(
                lookup_type="market_data",
                execution_time=execution_time,
                status="success",
                is_mock=True
            )
            
            return mock_data
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error al buscar datos de mercado: {str(e)}")
            
            self.metrics.record_lookup_execution(
                lookup_type="market_data",
                execution_time=execution_time,
                status="error",
                error=str(e)
            )
            
            return {
                "error": f"Error al buscar datos de mercado: {str(e)}",
                "source": "Error",
                "timestamp": time.time()
            }
    
    def search_news(self, query: str) -> Dict[str, Any]:
        """
        Busca noticias relevantes para la consulta.
        
        Args:
            query: Consulta sobre noticias
            
        Returns:
            Noticias encontradas
        """
        start_time = time.time()
        
        try:
            logger.info(f"Buscando noticias para: {query[:50]}...")
            
            # Intentar usar News API si hay clave disponible
            if self.api_keys.get("news_api"):
                try:
                    # Preparar parámetros para News API
                    params = {
                        "q": query,
                        "language": "es",
                        "sortBy": "relevancy",
                        "pageSize": 5,
                        "apiKey": self.api_keys["news_api"]
                    }
                    
                    url = f"https://newsapi.org/v2/everything?{urlencode(params)}"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "articles" in data and data["articles"]:
                            execution_time = time.time() - start_time
                            self.metrics.record_lookup_execution(
                                lookup_type="news",
                                execution_time=execution_time,
                                status="success"
                            )
                            
                            return {
                                "articles": data["articles"],
                                "total_results": data.get("totalResults", len(data["articles"])),
                                "source": "News API",
                                "timestamp": time.time()
                            }
                
                except Exception as e:
                    logger.warning(f"Error al obtener noticias de News API: {str(e)}")
            
            # Si no hay clave o falló la búsqueda, generar datos simulados
            logger.info("Usando noticias simuladas")
            mock_news = self._generate_mock_news(query)
            
            execution_time = time.time() - start_time
            self.metrics.record_lookup_execution(
                lookup_type="news",
                execution_time=execution_time,
                status="success",
                is_mock=True
            )
            
            return mock_news
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error al buscar noticias: {str(e)}")
            
            self.metrics.record_lookup_execution(
                lookup_type="news",
                execution_time=execution_time,
                status="error",
                error=str(e)
            )
            
            return {
                "error": f"Error al buscar noticias: {str(e)}",
                "source": "Error",
                "timestamp": time.time()
            }
    
    def search_industry_reports(self, industry: str) -> Dict[str, Any]:
        """
        Busca informes de industria.
        
        Args:
            industry: Nombre de la industria
            
        Returns:
            Informes de la industria
        """
        start_time = time.time()
        
        try:
            logger.info(f"Buscando informes para industria: {industry}")
            
            # Simulación de datos ya que no hay API real
            mock_reports = self._generate_mock_industry_reports(industry)
            
            execution_time = time.time() - start_time
            self.metrics.record_lookup_execution(
                lookup_type="industry",
                execution_time=execution_time,
                status="success",
                is_mock=True
            )
            
            return mock_reports
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error al buscar informes de industria: {str(e)}")
            
            self.metrics.record_lookup_execution(
                lookup_type="industry",
                execution_time=execution_time,
                status="error",
                error=str(e)
            )
            
            return {
                "error": f"Error al buscar informes de industria: {str(e)}",
                "source": "Error",
                "timestamp": time.time()
            }
    
    def search_web(self, query: str) -> Dict[str, Any]:
        """
        Busca información en la web.
        
        Args:
            query: Consulta para buscar en la web
            
        Returns:
            Resultados de la búsqueda web
        """
        start_time = time.time()
        
        try:
            logger.info(f"Buscando información web para: {query[:50]}...")
            
            # Intentar usar Bing Search API si hay clave disponible
            if self.api_keys.get("bing_search"):
                try:
                    # Preparar parámetros para Bing Search
                    headers = {
                        "Ocp-Apim-Subscription-Key": self.api_keys["bing_search"]
                    }
                    
                    params = {
                        "q": query,
                        "count": 5,
                        "offset": 0,
                        "mkt": "es-ES"
                    }
                    
                    url = f"https://api.bing.microsoft.com/v7.0/search?{urlencode(params)}"
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "webPages" in data and "value" in data["webPages"]:
                            execution_time = time.time() - start_time
                            self.metrics.record_lookup_execution(
                                lookup_type="web",
                                execution_time=execution_time,
                                status="success"
                            )
                            
                            return {
                                "results": data["webPages"]["value"],
                                "total_results": data["webPages"].get("totalEstimatedMatches", 0),
                                "source": "Bing Search API",
                                "timestamp": time.time()
                            }
                
                except Exception as e:
                    logger.warning(f"Error al obtener resultados de Bing Search: {str(e)}")
            
            # Si no hay clave o falló la búsqueda, generar datos simulados
            logger.info("Usando resultados web simulados")
            mock_web = self._generate_mock_web_results(query)
            
            execution_time = time.time() - start_time
            self.metrics.record_lookup_execution(
                lookup_type="web",
                execution_time=execution_time,
                status="success",
                is_mock=True
            )
            
            return mock_web
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error al buscar información web: {str(e)}")
            
            self.metrics.record_lookup_execution(
                lookup_type="web",
                execution_time=execution_time,
                status="error",
                error=str(e)
            )
            
            return {
                "error": f"Error al buscar información web: {str(e)}",
                "source": "Error",
                "timestamp": time.time()
            }
    
    def lookup_company_data(self, company: str) -> Dict[str, Any]:
        """
        Busca información sobre una empresa.
        
        Args:
            company: Nombre de la empresa
            
        Returns:
            Datos de la empresa
        """
        start_time = time.time()
        
        try:
            logger.info(f"Buscando información de empresa: {company}")
            
            # Simulación de datos ya que no hay API real
            mock_company = self._generate_mock_company_data(company)
            
            execution_time = time.time() - start_time
            self.metrics.record_lookup_execution(
                lookup_type="company",
                execution_time=execution_time,
                status="success",
                is_mock=True
            )
            
            return mock_company
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error al buscar información de empresa: {str(e)}")
            
            self.metrics.record_lookup_execution(
                lookup_type="company",
                execution_time=execution_time,
                status="error",
                error=str(e)
            )
            
            return {
                "error": f"Error al buscar información de empresa: {str(e)}",
                "source": "Error",
                "timestamp": time.time()
            }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la búsqueda según los parámetros proporcionados.
        Método principal para compatibilidad con el servidor MCP.
        
        Args:
            params: Parámetros para la búsqueda
            
        Returns:
            Resultados de la búsqueda
        """
        lookup_type = params.get("lookup_type", "general")
        query = params.get("query", "")
        
        if lookup_type == "market_data":
            return self.search_market_data(query)
        elif lookup_type == "news":
            return self.search_news(query)
        elif lookup_type == "industry":
            industry = params.get("industry", "")
            return self.search_industry_reports(industry)
        elif lookup_type == "web":
            return self.search_web(query)
        elif lookup_type == "company":
            company = params.get("company", "")
            return self.lookup_company_data(company)
        elif lookup_type == "general":
            # Para una búsqueda general, combinar resultados de varias fuentes
            results = {}
            
            # Búsqueda de mercado
            market_data = self.search_market_data(query)
            if "error" not in market_data:
                results["market_data"] = market_data
            
            # Búsqueda de noticias
            news_data = self.search_news(query)
            if "error" not in news_data:
                results["news"] = news_data
            
            # Búsqueda web
            web_data = self.search_web(query)
            if "error" not in web_data:
                results["web"] = web_data
            
            return {
                "results": results,
                "lookup_type": "general",
                "query": query,
                "timestamp": time.time()
            }
        else:
            return {
                "error": f"Tipo de búsqueda no válido: {lookup_type}",
                "valid_types": ["market_data", "news", "industry", "web", "company", "general"]
            }
    
    # Métodos auxiliares para extracción y generación de datos simulados
    
    def _extract_market_symbols(self, query: str) -> List[str]:
        """Extrae posibles símbolos de mercado de la consulta."""
        # Símbolos comunes para simular extracción
        common_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NFLX"]
        
        # En un sistema real, esto usaría NLP para identificar entidades
        # y mapearlas a símbolos bursátiles
        return random.sample(common_symbols, min(3, len(common_symbols)))
    
    def _generate_mock_market_data(self, query: str) -> Dict[str, Any]:
        """Genera datos de mercado simulados basados en la consulta."""
        symbols = self._extract_market_symbols(query)
        results = {}
        
        for symbol in symbols:
            price = round(random.uniform(50, 500), 2)
            change = round(random.uniform(-5, 5), 2)
            percent_change = round((change / price) * 100, 2)
            
            results[symbol] = {
                "01. symbol": symbol,
                "02. open": str(round(price - random.uniform(0, 10), 2)),
                "03. high": str(round(price + random.uniform(0, 15), 2)),
                "04. low": str(round(price - random.uniform(0, 15), 2)),
                "05. price": str(price),
                "06. volume": str(int(random.uniform(1000000, 10000000))),
                "07. latest trading day": "2024-01-15",
                "08. previous close": str(round(price - change, 2)),
                "09. change": str(change),
                "10. change percent": f"{percent_change}%"
            }
        
        return {
            "data": results,
            "source": "Datos simulados",
            "timestamp": time.time()
        }
    
    def _generate_mock_news(self, query: str) -> Dict[str, Any]:
        """Genera noticias simuladas basadas en la consulta."""
        articles = []
        words = query.split()
        
        for i in range(5):
            title_words = random.sample(words, min(len(words), 3))
            title = "Noticia importante sobre " + " ".join(title_words)
            
            articles.append({
                "source": {"id": f"source-{i}", "name": f"Fuente {i+1}"},
                "author": f"Autor {i+1}",
                "title": title,
                "description": f"Descripción detallada sobre {' '.join(random.sample(words, min(len(words), 4)))}.",
                "url": f"https://example.com/news/{i}",
                "urlToImage": f"https://example.com/images/news{i}.jpg",
                "publishedAt": "2024-01-15T12:00:00Z",
                "content": f"Contenido completo del artículo relacionado con {query}..."
            })
        
        return {
            "articles": articles,
            "total_results": 5,
            "source": "Noticias simuladas",
            "timestamp": time.time()
        }
    
    def _generate_mock_industry_reports(self, industry: str) -> Dict[str, Any]:
        """Genera informes de industria simulados."""
        reports = []
        
        for i in range(3):
            reports.append({
                "title": f"Informe {i+1} sobre {industry}",
                "author": f"Consultora {i+1}",
                "date": "2024-01-15",
                "summary": f"Resumen del informe {i+1} sobre tendencias en {industry}.",
                "url": f"https://example.com/reports/{industry}/{i}",
                "key_findings": [
                    f"Hallazgo importante 1 sobre {industry}",
                    f"Hallazgo importante 2 sobre {industry}",
                    f"Hallazgo importante 3 sobre {industry}"
                ]
            })
        
        return {
            "reports": reports,
            "industry": industry,
            "source": "Informes simulados",
            "timestamp": time.time()
        }
    
    def _generate_mock_web_results(self, query: str) -> Dict[str, Any]:
        """Genera resultados web simulados basados en la consulta."""
        results = []
        words = query.split()
        
        for i in range(5):
            title_words = random.sample(words, min(len(words), 3))
            title = "Página web sobre " + " ".join(title_words)
            
            results.append({
                "id": f"result-{i}",
                "name": title,
                "url": f"https://example.com/result/{i}",
                "snippet": f"Fragmento de texto que menciona {' '.join(random.sample(words, min(len(words), 4)))}...",
                "dateLastCrawled": "2024-01-15T12:00:00Z"
            })
        
        return {
            "results": results,
            "total_results": 100,
            "source": "Resultados web simulados",
            "timestamp": time.time()
        }
    
    def _generate_mock_company_data(self, company: str) -> Dict[str, Any]:
        """Genera datos de empresa simulados."""
        return {
            "name": company,
            "symbol": ''.join([c[0] for c in company.split() if c]),
            "description": f"Descripción de {company}, empresa líder en su sector.",
            "industry": random.choice(["Tecnología", "Finanzas", "Salud", "Retail", "Manufactura"]),
            "founded": str(random.randint(1950, 2020)),
            "headquarters": random.choice(["Nueva York", "San Francisco", "Londres", "Tokio", "Madrid"]),
            "ceo": f"Ejecutivo de {company}",
            "employees": random.randint(100, 50000),
            "revenue": f"${random.randint(1, 100)} mil millones",
            "website": f"https://www.{company.lower().replace(' ', '')}.com",
            "source": "Datos de empresa simulados",
            "timestamp": time.time()
        }

async def buscar_datos_financieros(empresa: str, periodo: Optional[str] = None) -> Dict[str, Any]:
    """
    Busca datos financieros de una empresa específica.
    
    Args:
        empresa: Nombre o ticker de la empresa
        periodo: Periodo para los datos (trimestre/año). Si no se especifica, se usa el último disponible.
    
    Returns:
        Datos financieros de la empresa
    """
    # En una implementación real, esto conectaría con una API financiera
    # Para demostración, generamos datos de ejemplo
    
    hoy = datetime.now()
    periodo_actual = periodo or f"Q{(hoy.month-1)//3 + 1} {hoy.year}"
    
    # Empresas comunes con datos preestablecidos para demostración
    empresas_conocidas = {
        "tesla": {
            "nombre": "Tesla, Inc.",
            "ticker": "TSLA",
            "sector": "Automotriz/Tecnología",
            "ingresos": 24578000000,
            "beneficio_neto": 2515000000,
            "activos_totales": 84526000000,
            "pasivos_totales": 48109000000,
            "flujo_caja": 4591000000,
            "margen_beneficio": 0.102,
            "ROI": 0.093,
        },
        "apple": {
            "nombre": "Apple Inc.",
            "ticker": "AAPL",
            "sector": "Tecnología",
            "ingresos": 94836000000,
            "beneficio_neto": 22955000000,
            "activos_totales": 336307000000,
            "pasivos_totales": 290452000000,
            "flujo_caja": 28869000000,
            "margen_beneficio": 0.242,
            "ROI": 0.175,
        },
        "microsoft": {
            "nombre": "Microsoft Corporation",
            "ticker": "MSFT",
            "sector": "Tecnología",
            "ingresos": 51865000000,
            "beneficio_neto": 16425000000,
            "activos_totales": 301366000000,
            "pasivos_totales": 193694000000,
            "flujo_caja": 19965000000,
            "margen_beneficio": 0.317,
            "ROI": 0.186,
        },
        "amazon": {
            "nombre": "Amazon.com, Inc.",
            "ticker": "AMZN",
            "sector": "Comercio electrónico/Tecnología",
            "ingresos": 134373000000,
            "beneficio_neto": 4358000000,
            "activos_totales": 370151000000,
            "pasivos_totales": 282304000000,
            "flujo_caja": 6354000000,
            "margen_beneficio": 0.032,
            "ROI": 0.112,
        },
    }
    
    # Buscar la empresa (ignorando mayúsculas/minúsculas)
    empresa_lower = empresa.lower()
    empresa_data = None
    
    for key, data in empresas_conocidas.items():
        if key == empresa_lower or data["ticker"].lower() == empresa_lower:
            empresa_data = data
            break
    
    # Si no se encuentra, crear datos aleatorios
    if empresa_data is None:
        empresa_data = {
            "nombre": empresa,
            "ticker": empresa[:4].upper(),
            "sector": "General",
            "ingresos": random.randint(10000000, 500000000),
            "beneficio_neto": random.randint(1000000, 100000000),
            "activos_totales": random.randint(50000000, 1000000000),
            "pasivos_totales": random.randint(20000000, 500000000),
            "flujo_caja": random.randint(1000000, 50000000),
            "margen_beneficio": round(random.uniform(0.05, 0.3), 3),
            "ROI": round(random.uniform(0.05, 0.25), 3),
        }
    
    # Añadir variación por periodo
    variacion = random.uniform(0.9, 1.1)
    
    return {
        "empresa": empresa_data["nombre"],
        "ticker": empresa_data["ticker"],
        "sector": empresa_data["sector"],
        "periodo": periodo_actual,
        "fecha_consulta": hoy.strftime("%Y-%m-%d"),
        "datos": {
            "ingresos": int(empresa_data["ingresos"] * variacion),
            "beneficio_neto": int(empresa_data["beneficio_neto"] * variacion),
            "activos_totales": int(empresa_data["activos_totales"] * variacion),
            "pasivos_totales": int(empresa_data["pasivos_totales"] * variacion),
            "flujo_caja": int(empresa_data["flujo_caja"] * variacion),
            "margen_beneficio": round(empresa_data["margen_beneficio"] * variacion, 3),
            "ROI": round(empresa_data["ROI"] * variacion, 3),
        },
        "fuente": "Base de datos financiera Sesame (demo)",
        "actualizado": (hoy - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
    }

async def data_lookup(lookup_type: str, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Busca información general según el tipo de búsqueda y consulta.
    
    Args:
        lookup_type: Tipo de búsqueda ('market_data', 'news', 'company', etc.)
        query: Consulta de búsqueda
        filters: Filtros adicionales para la búsqueda
        
    Returns:
        Resultados de la búsqueda
    """
    # Inicializar resultado
    result = {
        "query": query,
        "tipo": lookup_type,
        "fecha_consulta": datetime.now().strftime("%Y-%m-%d"),
        "resultados": [],
        "fuente": "Servicio de datos Sesame (demo)",
        "success": True
    }
    
    # Aplicar filtros si existen
    filter_str = ""
    if filters:
        filter_str = " con filtros: " + ", ".join([f"{k}={v}" for k, v in filters.items()])
    
    # Procesar según el tipo de búsqueda
    if lookup_type == "market_data":
        result["resultados"] = generar_datos_mercado(query)
        result["descripcion"] = f"Datos de mercado para '{query}'{filter_str}"
    elif lookup_type == "news":
        result["resultados"] = generar_noticias(query)
        result["descripcion"] = f"Noticias relacionadas con '{query}'{filter_str}"
    elif lookup_type == "company":
        result["resultados"] = generar_datos_empresa(query)
        result["descripcion"] = f"Información de la empresa '{query}'{filter_str}"
    else:
        result["resultados"] = []
        result["success"] = False
        result["error"] = f"Tipo de búsqueda '{lookup_type}' no soportado"
    
    return result

def generar_datos_mercado(query: str) -> List[Dict[str, Any]]:
    """Genera datos de mercado de ejemplo para una consulta."""
    hoy = datetime.now()
    
    # Generar datos para los últimos 5 días
    datos = []
    for i in range(5):
        fecha = hoy - timedelta(days=i)
        variacion = random.uniform(-2.0, 2.0)
        datos.append({
            "fecha": fecha.strftime("%Y-%m-%d"),
            "indice_principal": round(3500 + random.uniform(-100, 100), 2),
            "volumen_mercado": random.randint(1000000, 5000000),
            "variacion": round(variacion, 2),
            "tendencia": "alza" if variacion > 0 else "baja",
            "volatilidad": round(random.uniform(10, 30), 2)
        })
    
    return datos

def generar_noticias(query: str) -> List[Dict[str, Any]]:
    """Genera noticias de ejemplo relacionadas con una consulta."""
    hoy = datetime.now()
    
    # Noticias de ejemplo
    titulares = [
        f"Resultados trimestrales de {query} superan expectativas",
        f"Nuevas tendencias afectan al sector de {query}",
        f"Expertos analizan el futuro de {query} en el mercado global",
        f"Regulaciones podrían impactar la industria de {query}",
        f"Innovación: {query} lidera transformación digital"
    ]
    
    noticias = []
    for i, titular in enumerate(titulares):
        fecha = hoy - timedelta(days=i)
        noticias.append({
            "titulo": titular,
            "fecha": fecha.strftime("%Y-%m-%d"),
            "fuente": random.choice(["Financial Times", "Bloomberg", "CNBC", "Reuters", "The Wall Street Journal"]),
            "resumen": f"Breve resumen de la noticia sobre {query} y su impacto en el mercado financiero.",
            "relevancia": round(random.uniform(0.5, 1.0), 2),
            "sentiment": random.choice(["positivo", "neutral", "negativo"])
        })
    
    return noticias

def generar_datos_empresa(query: str) -> Dict[str, Any]:
    """Genera información detallada de una empresa de ejemplo."""
    return {
        "nombre": query,
        "ticker": query[:4].upper(),
        "sede": random.choice(["Nueva York, EEUU", "San Francisco, EEUU", "Londres, UK", "Tokyo, Japón"]),
        "fundacion": random.randint(1950, 2010),
        "sector": random.choice(["Tecnología", "Finanzas", "Manufactura", "Servicios", "Energía"]),
        "empleados": random.randint(1000, 100000),
        "revenue_anual": f"${random.randint(100, 1000)} millones",
        "cotizacion": random.choice([True, False]),
        "productos_principales": [f"Producto {i+1}" for i in range(3)],
        "ultimo_precio_accion": round(random.uniform(10, 500), 2),
        "variacion_precio": round(random.uniform(-5, 5), 2),
        "capitalizacion": f"${random.randint(1, 100)} mil millones"
    } 
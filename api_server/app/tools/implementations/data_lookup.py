"""
Implementación de herramienta para búsqueda de datos externos.
"""

import random
import time
from typing import Any
from urllib.parse import urlencode

import requests

from app.core.config import get_settings
from app.core.logging import logger
from app.core.metrics import MetricsCollector

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

    def search_market_data(self, term=None, **kwargs):
        """
        Busca datos de mercado relacionados con el término de búsqueda.
        
        Args:
            term: Término de búsqueda
            kwargs: Argumentos adicionales para la búsqueda
            
        Returns:
            Datos de mercado encontrados
        """
        try:
            start_time = time.time()
            query = term if term else (kwargs.get("query") or "")

            # Logueamos solo los primeros 50 caracteres de la consulta como texto
            query_preview = query[:50] + "..." if len(query) > 50 else query
            logger.info(f"Buscando datos de mercado para: {query_preview}")

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

    def search_news(self, term=None, **kwargs):
        """
        Busca noticias relacionadas con el término de búsqueda.
        
        Args:
            term: Término de búsqueda
            kwargs: Argumentos adicionales para la búsqueda
            
        Returns:
            Noticias encontradas
        """
        try:
            start_time = time.time()
            query = term if term else (kwargs.get("query") or "")

            # Logueamos solo los primeros 50 caracteres de la consulta como texto
            query_preview = query[:50] + "..." if len(query) > 50 else query
            logger.info(f"Buscando noticias para: {query_preview}")

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

    def search_industry_reports(self, industry: str) -> dict[str, Any]:
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

    def search_web(self, term=None, **kwargs):
        """
        Busca información en la web relacionada con el término de búsqueda.
        
        Args:
            term: Término de búsqueda
            kwargs: Argumentos adicionales para la búsqueda
            
        Returns:
            Información web encontrada
        """
        try:
            start_time = time.time()
            query = term if term else (kwargs.get("query") or "")

            # Logueamos solo los primeros 50 caracteres de la consulta como texto
            query_preview = query[:50] + "..." if len(query) > 50 else query
            logger.info(f"Buscando información web para: {query_preview}")

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

    def lookup_company_data(self, company: str) -> dict[str, Any]:
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

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
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

    def _extract_market_symbols(self, query: str) -> list[str]:
        """Extrae posibles símbolos de mercado de la consulta."""
        # Símbolos comunes para simular extracción
        common_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NFLX"]

        # En un sistema real, esto usaría NLP para identificar entidades
        # y mapearlas a símbolos bursátiles
        return random.sample(common_symbols, min(3, len(common_symbols)))

    def _generate_mock_market_data(self, query: str) -> dict[str, Any]:
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

    def _generate_mock_news(self, query: str) -> dict[str, Any]:
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

    def _generate_mock_industry_reports(self, industry: str) -> dict[str, Any]:
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

    def _generate_mock_web_results(self, query: str) -> dict[str, Any]:
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

    def _generate_mock_company_data(self, company: str) -> dict[str, Any]:
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

from unittest.mock import MagicMock, patch

import pytest
import requests

from app.services.data_lookup import DataLookupService


@pytest.fixture
def data_lookup_service():
    """Fixture para crear una instancia de DataLookupService."""
    return DataLookupService(
        alpha_vantage_api_key="test_av_key",
        news_api_key="test_news_key",
        bing_search_api_key="test_bing_key"
    )

def test_search_market_data(data_lookup_service):
    """Test de búsqueda de datos de mercado."""
    # Configurar respuesta simulada para requests.get
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "price": 150.25,
                "change": 2.5,
                "market_cap": "2.5T"
            }
        ]
    }

    with patch('requests.get', return_value=mock_response):
        result = data_lookup_service.search_market_data("Apple")

    assert "results" in result
    assert len(result["results"]) == 1
    assert result["results"][0]["symbol"] == "AAPL"
    assert "processing_time" in result

def test_search_market_data_error(data_lookup_service):
    """Test del manejo de errores en búsqueda de datos de mercado."""
    # Simular error en la solicitud
    with patch('requests.get', side_effect=requests.exceptions.RequestException("Error de conexión")):
        result = data_lookup_service.search_market_data("Apple")

    assert "error" in result
    assert "Error al obtener datos de mercado" in result["error"]
    assert "results" in result
    assert len(result["results"]) == 0

def test_search_news(data_lookup_service):
    """Test de búsqueda de noticias."""
    # Configurar respuesta simulada
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "articles": [
            {
                "title": "Noticia de prueba",
                "description": "Descripción de prueba",
                "url": "http://example.com/news",
                "publishedAt": "2023-09-01T12:00:00Z",
                "source": {"name": "Example News"}
            }
        ]
    }

    with patch('requests.get', return_value=mock_response):
        result = data_lookup_service.search_news("fintech")

    assert "results" in result
    assert len(result["results"]) == 1
    assert result["results"][0]["title"] == "Noticia de prueba"
    assert "processing_time" in result

def test_search_industry_reports(data_lookup_service):
    """Test de búsqueda de informes de industria."""
    result = data_lookup_service.search_industry_reports("fintech")

    assert "results" in result
    assert len(result["results"]) > 0
    assert "title" in result["results"][0]
    assert "url" in result["results"][0]
    assert "processing_time" in result

def test_search_web(data_lookup_service):
    """Test de búsqueda en la web."""
    # Configurar respuesta simulada
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "webPages": {
            "value": [
                {
                    "name": "Resultado de prueba",
                    "url": "http://example.com/result",
                    "snippet": "Extracto de prueba"
                }
            ]
        }
    }

    with patch('requests.get', return_value=mock_response):
        result = data_lookup_service.search_web("fintech latinoamerica")

    assert "results" in result
    assert len(result["results"]) == 1
    assert result["results"][0]["title"] == "Resultado de prueba"
    assert "processing_time" in result

def test_lookup_company_data(data_lookup_service):
    """Test de búsqueda de datos de empresa."""
    # Configurar respuesta simulada
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "company": {
            "name": "Nubank",
            "industry": "Fintech",
            "founded": 2013,
            "headquarters": "São Paulo, Brasil",
            "revenue": "$1.5B"
        }
    }

    with patch('requests.get', return_value=mock_response):
        result = data_lookup_service.lookup_company_data("Nubank")

    assert "company" in result
    assert result["company"]["name"] == "Nubank"
    assert "processing_time" in result

def test_lookup_company_data_fallback(data_lookup_service):
    """Test del uso de datos simulados cuando falla la API."""
    # Simular error en la solicitud
    with patch('requests.get', side_effect=requests.exceptions.RequestException("Error de conexión")):
        result = data_lookup_service.lookup_company_data("Nubank")

    # Verificar que devuelve datos simulados en caso de error
    assert "company" in result
    assert "name" in result["company"]
    assert "industry" in result["company"]
    assert "error" in result

class TestDataLookupService:
    """Pruebas para el servicio DataLookupService."""

    def setup_method(self):
        """Configuración inicial para cada prueba."""
        self.service = DataLookupService(
            alpha_vantage_api_key="test_av_key",
            news_api_key="test_news_key",
            bing_search_api_key="test_bing_key"
        )

    @patch('requests.get')
    def test_search_market_data_success(self, mock_get):
        """Prueba la búsqueda de datos de mercado exitosa."""
        # Configurar mock de respuesta
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Meta Data": {
                "1. Information": "Daily Prices and Volumes for Test Stock",
                "2. Symbol": "TSLA"
            },
            "Time Series (Daily)": {
                "2023-10-20": {
                    "1. open": "220.53",
                    "2. high": "222.25",
                    "3. low": "217.91",
                    "4. close": "220.11",
                    "5. volume": "12345678"
                }
            }
        }
        mock_get.return_value = mock_response

        # Ejecutar búsqueda
        result = self.service.search_market_data("TSLA")

        # Verificar llamada a API
        mock_get.assert_called_once()

        # Verificar resultados
        assert result["status"] == "success"
        assert "data" in result
        assert "TSLA" in str(result["data"])
        assert "processing_time" in result

    @patch('requests.get')
    def test_search_market_data_error(self, mock_get):
        """Prueba el manejo de errores en búsqueda de datos de mercado."""
        # Configurar mock para generar error
        mock_get.side_effect = requests.RequestException("API error")

        # Ejecutar búsqueda
        result = self.service.search_market_data("TSLA")

        # Verificar resultados de error
        assert result["status"] == "error"
        assert "error" in result
        assert "API error" in result["error"]
        assert "processing_time" in result

    @patch('requests.get')
    def test_search_news_success(self, mock_get):
        """Prueba la búsqueda de noticias exitosa."""
        # Configurar mock de respuesta
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "totalResults": 2,
            "articles": [
                {
                    "source": {"id": "bbc-news", "name": "BBC News"},
                    "author": "BBC News",
                    "title": "Test Article 1",
                    "description": "Description of test article 1",
                    "url": "https://www.bbc.com/news/test1",
                    "publishedAt": "2023-10-20T12:00:00Z"
                },
                {
                    "source": {"id": "reuters", "name": "Reuters"},
                    "author": "Reuters Staff",
                    "title": "Test Article 2",
                    "description": "Description of test article 2",
                    "url": "https://www.reuters.com/news/test2",
                    "publishedAt": "2023-10-19T15:30:00Z"
                }
            ]
        }
        mock_get.return_value = mock_response

        # Ejecutar búsqueda
        result = self.service.search_news("business finance")

        # Verificar llamada a API
        mock_get.assert_called_once()

        # Verificar resultados
        assert result["status"] == "success"
        assert "data" in result
        assert len(result["data"]["articles"]) == 2
        assert "Test Article 1" in str(result["data"])
        assert "processing_time" in result

    @patch('requests.get')
    def test_search_industry_reports_success(self, mock_get):
        """Prueba la búsqueda de informes de industria exitosa."""
        # Configurar mock de respuesta
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "reports": [
                {
                    "title": "Tech Industry Report 2023",
                    "source": "Research Firm A",
                    "url": "https://example.com/reports/tech2023",
                    "published_date": "2023-09-15",
                    "summary": "Comprehensive analysis of tech industry trends."
                },
                {
                    "title": "Technology Market Outlook",
                    "source": "Research Firm B",
                    "url": "https://example.com/reports/tech-outlook",
                    "published_date": "2023-08-22",
                    "summary": "Future prospects for the technology sector."
                }
            ]
        }
        mock_get.return_value = mock_response

        # Ejecutar búsqueda
        result = self.service.search_industry_reports("technology")

        # Verificar llamada a API
        mock_get.assert_called_once()

        # Verificar resultados
        assert result["status"] == "success"
        assert "data" in result
        assert len(result["data"]["reports"]) == 2
        assert "Tech Industry Report" in str(result["data"])
        assert "processing_time" in result

    @patch('requests.get')
    def test_search_web_success(self, mock_get):
        """Prueba la búsqueda web exitosa."""
        # Configurar mock de respuesta
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "webPages": {
                "totalEstimatedMatches": 10000,
                "value": [
                    {
                        "name": "Test Web Page 1",
                        "url": "https://example.com/page1",
                        "snippet": "This is a snippet from the first test page."
                    },
                    {
                        "name": "Test Web Page 2",
                        "url": "https://example.com/page2",
                        "snippet": "This is a snippet from the second test page."
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        # Ejecutar búsqueda
        result = self.service.search_web("test query")

        # Verificar llamada a API
        mock_get.assert_called_once()

        # Verificar resultados
        assert result["status"] == "success"
        assert "data" in result
        assert len(result["data"]["webPages"]["value"]) == 2
        assert "Test Web Page 1" in str(result["data"])
        assert "processing_time" in result

    @patch('requests.get')
    def test_lookup_company_data_success(self, mock_get):
        """Prueba la búsqueda de datos de empresa exitosa."""
        # Configurar mock de respuesta
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "employees": 154000,
            "headquarters": "Cupertino, California",
            "founded": 1976,
            "ceo": "Tim Cook",
            "website": "https://www.apple.com",
            "financials": {
                "market_cap": "2.5T",
                "pe_ratio": 28.5,
                "revenue_ttm": "365.82B",
                "revenue_growth": 0.075,
                "profit_margin": 0.25
            }
        }
        mock_get.return_value = mock_response

        # Ejecutar búsqueda
        result = self.service.lookup_company_data("Apple")

        # Verificar llamada a API
        mock_get.assert_called_once()

        # Verificar resultados
        assert result["status"] == "success"
        assert "data" in result
        assert result["data"]["company_name"] == "Apple Inc."
        assert "financials" in result["data"]
        assert "processing_time" in result

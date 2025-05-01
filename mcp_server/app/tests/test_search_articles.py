"""
Tests para las funcionalidades de search_articles.py
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.tools.implementations.search_articles import search_articles


class TestSearchArticles:
    """Pruebas para las funciones de búsqueda de artículos."""

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_search_articles_simple_query(self, mock_get):
        """Prueba una búsqueda simple de artículos."""
        # Configurar respuesta simulada
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "search": [
                    {
                        "title": "El mercado financiero",
                        "snippet": "Análisis del comportamiento del mercado financiero...",
                    },
                    {
                        "title": "Tendencias económicas",
                        "snippet": "Previsiones económicas para el segundo semestre...",
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        # Datos de prueba
        query = "mercado financiero"
        
        # Ejecutar la función
        resultado = await search_articles(query=query)
        
        # Verificar resultados
        assert "tema" in resultado
        assert "num_resultados" in resultado
        assert "fecha_busqueda" in resultado
        assert "articulos" in resultado
        
        # Verificar que devuelve los artículos esperados
        assert len(resultado["articulos"]) == 2
        assert resultado["articulos"][0]["titulo"] == "El mercado financiero"
        assert resultado["articulos"][1]["titulo"] == "Tendencias económicas"
        assert resultado["num_resultados"] == 2

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_search_articles_with_tema(self, mock_get):
        """Prueba una búsqueda usando el parámetro tema."""
        # Configurar respuesta simulada
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "search": [
                    {
                        "title": "Estrategias de inversión",
                        "snippet": "Estrategias recomendadas para inversores...",
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        # Datos de prueba
        tema = "estrategias inversión"
        max_resultados = 3
        
        # Ejecutar la función
        resultado = await search_articles(
            tema=tema,
            max_resultados=max_resultados
        )
        
        # Verificar resultados
        assert "tema" in resultado
        assert "num_resultados" in resultado
        assert "fecha_busqueda" in resultado
        assert "articulos" in resultado
        
        # Verificar que el tema se usó correctamente
        assert resultado["tema"] == tema
        
        # Verificar que devuelve el artículo esperado
        assert len(resultado["articulos"]) == 1
        assert resultado["articulos"][0]["titulo"] == "Estrategias de inversión"
        assert resultado["articulos"][0]["fuente"] == "Wikipedia"

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_search_articles_no_results(self, mock_get):
        """Prueba una búsqueda que no devuelve resultados."""
        # Configurar respuesta simulada
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "search": []
            }
        }
        mock_get.return_value = mock_response
        
        # Datos de prueba
        query = "término muy específico sin resultados"
        
        # Ejecutar la función
        resultado = await search_articles(query=query)
        
        # Verificar resultados
        assert "tema" in resultado
        assert "num_resultados" in resultado
        assert "fecha_busqueda" in resultado
        assert "articulos" in resultado
        
        # Verificar que devuelve una lista vacía de resultados
        assert len(resultado["articulos"]) == 0
        assert resultado["num_resultados"] == 0

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_search_articles_api_error(self, mock_get):
        """Prueba el manejo de errores de la API."""
        # Configurar respuesta simulada con error
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Datos de prueba
        query = "consulta normal"
        
        # Ejecutar la función
        resultado = await search_articles(query=query)
        
        # Verificar que se muestra un mensaje de error
        assert "error" in resultado
        assert "404" in resultado["error"]

    @pytest.mark.asyncio
    async def test_search_articles_missing_params(self):
        """Prueba el manejo de error cuando faltan parámetros necesarios."""
        # Ejecutar la función sin query ni tema
        resultado = await search_articles()
        
        # Verificar que hay un mensaje de error
        assert "error" in resultado
        assert "Debe proporcionar un parámetro" in resultado["error"] 
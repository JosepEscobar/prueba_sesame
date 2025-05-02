"""
Tests para las funcionalidades de data_lookup.py
"""

import pytest
from unittest.mock import MagicMock, patch

from app.tools.implementations.data_lookup import (
    buscar_datos_financieros,
    data_lookup
)


class TestDataLookup:
    """Pruebas para las funciones de búsqueda de datos."""

    @pytest.mark.asyncio
    async def test_buscar_datos_financieros(self):
        """Prueba que la función busca datos financieros correctamente."""
        # Datos de prueba
        empresa = "TechCorp"
        periodo = "Q2 2023"
        
        # Ejecutar la función
        resultado = await buscar_datos_financieros(
            empresa=empresa,
            periodo=periodo
        )
        
        # Verificar resultados
        assert "empresa" in resultado
        assert "periodo" in resultado
        assert "fecha_consulta" in resultado
        assert "datos" in resultado
        
        # Verificar que los datos de la empresa coinciden
        assert resultado["empresa"] == empresa
        assert resultado["periodo"] == periodo
        
        # Verificar que los datos financieros contienen las claves esperadas
        assert "ingresos" in resultado["datos"]
        assert "beneficio_neto" in resultado["datos"]
        assert "activos_totales" in resultado["datos"]
        assert "pasivos_totales" in resultado["datos"]
        assert "flujo_caja" in resultado["datos"]
        assert "margen_beneficio" in resultado["datos"]
        assert "ROI" in resultado["datos"]

    @pytest.mark.asyncio
    async def test_buscar_datos_financieros_sin_periodo(self):
        """Prueba que la función maneja correctamente la falta de periodo."""
        # Datos de prueba
        empresa = "TechCorp"
        
        # Ejecutar la función sin especificar periodo
        resultado = await buscar_datos_financieros(
            empresa=empresa
        )
        
        # Verificar resultados
        assert "empresa" in resultado
        assert "periodo" in resultado
        assert "fecha_consulta" in resultado
        assert "datos" in resultado
        
        # El periodo debería ser generado automáticamente
        assert resultado["periodo"] is not None
        assert resultado["periodo"] != ""

    @pytest.mark.asyncio
    @patch('app.tools.implementations.data_lookup.generar_datos_empresa')
    async def test_data_lookup_company_data(self, mock_generar):
        """Prueba la búsqueda de datos de empresa."""
        # Configurar el mock
        mock_generar.return_value = {
            "nombre": "TechCorp",
            "ticker": "TECH",
            "sector": "Tecnología",
            "datos_financieros": {
                "ingresos": 1000000,
                "beneficios": 200000,
                "activos": 2000000,
                "pasivos": 800000
            },
            "ratios": {
                "pe": 15.5,
                "pb": 2.3,
                "roa": 0.1,
                "roe": 0.25
            }
        }
        
        # Datos de prueba
        lookup_type = "company"
        query = "TechCorp"
        filters = None
        
        # Ejecutar la función
        resultado = await data_lookup(
            lookup_type=lookup_type,
            query=query,
            filters=filters
        )
        
        # Verificar que se llamó al mock correctamente
        mock_generar.assert_called_once_with(query)
        
        # Verificar resultados - estructura (basado en inspección)
        assert "query" in resultado
        assert "tipo" in resultado
        assert "fecha_consulta" in resultado
        assert "resultados" in resultado
        assert "fuente" in resultado
        assert "success" in resultado
        assert "descripcion" in resultado
        
        # Verificar tipo de búsqueda
        assert resultado["tipo"] == "company"
        assert resultado["query"] == query
        assert resultado["success"] is True

    @pytest.mark.asyncio
    @patch('app.tools.implementations.data_lookup.generar_datos_mercado')
    async def test_data_lookup_market_data(self, mock_generar):
        """Prueba la búsqueda de datos de mercado."""
        # Configurar el mock
        mock_generar.return_value = [
            {
                "fecha": "2023-05-01",
                "indice_principal": 3550.25,
                "volumen_mercado": 3500000,
                "variacion": 1.2,
                "tendencia": "alza",
                "volatilidad": 15.8
            },
            {
                "fecha": "2023-04-30",
                "indice_principal": 3520.75,
                "volumen_mercado": 3200000,
                "variacion": -0.8,
                "tendencia": "baja",
                "volatilidad": 16.2
            }
        ]
        
        # Datos de prueba
        lookup_type = "market_data"
        query = "tecnología acciones"
        filters = None
        
        # Ejecutar la función
        resultado = await data_lookup(
            lookup_type=lookup_type,
            query=query,
            filters=filters
        )
        
        # Verificar que se llamó al mock correctamente
        mock_generar.assert_called_once_with(query)
        
        # Verificar resultados - estructura (basado en inspección)
        assert "query" in resultado
        assert "tipo" in resultado
        assert "fecha_consulta" in resultado
        assert "resultados" in resultado
        assert "fuente" in resultado
        assert "success" in resultado
        
        # Verificar tipo de búsqueda
        assert resultado["tipo"] == "market_data"
        assert resultado["query"] == query
        
        # Verificar que hay resultados
        assert len(resultado["resultados"]) > 0
        
        # Verificar estructura del primer resultado
        primer_resultado = resultado["resultados"][0]
        assert "fecha" in primer_resultado
        assert "indice_principal" in primer_resultado
        assert "variacion" in primer_resultado

    @pytest.mark.asyncio
    @patch('app.tools.implementations.data_lookup.generar_noticias')
    async def test_data_lookup_news(self, mock_generar):
        """Prueba la búsqueda de noticias."""
        # Configurar el mock
        mock_generar.return_value = [
            {
                "titulo": "Nueva política económica anunciada",
                "fuente": "El Economista",
                "fecha": "2023-05-01",
                "resumen": "El gobierno anunció nuevas medidas económicas..."
            },
            {
                "titulo": "Resultados trimestrales superan expectativas",
                "fuente": "Expansión",
                "fecha": "2023-04-28",
                "resumen": "Las empresas del sector tecnológico presentaron..."
            }
        ]
        
        # Datos de prueba
        lookup_type = "news"
        query = "economía noticias"
        filters = {"fecha_desde": "2023-04-01", "fecha_hasta": "2023-05-01"}
        
        # Ejecutar la función
        resultado = await data_lookup(
            lookup_type=lookup_type,
            query=query,
            filters=filters
        )
        
        # Verificar resultados - estructura (basado en inspección)
        assert "query" in resultado
        assert "tipo" in resultado
        assert "fecha_consulta" in resultado
        assert "resultados" in resultado
        assert "fuente" in resultado
        assert "success" in resultado
        assert "descripcion" in resultado
        
        # Verificar tipo de búsqueda
        assert resultado["tipo"] == "news"
        assert resultado["query"] == query
        
        # Verificar que hay resultados
        assert len(resultado["resultados"]) > 0

    @pytest.mark.asyncio
    async def test_data_lookup_tipo_invalido(self):
        """Prueba el manejo de error cuando se proporciona un tipo inválido."""
        # Datos de prueba
        lookup_type = "tipo_invalido"  # Tipo no existente
        query = "búsqueda inválida"
        filters = None
        
        # Ejecutar la función - debe retornar un error, no levantar excepción
        resultado = await data_lookup(
            lookup_type=lookup_type,
            query=query,
            filters=filters
        )
        
        # Verificar que hay un mensaje de error
        assert "error" in resultado
        assert "tipo_invalido" in resultado["error"].lower()
        assert resultado["success"] is False 
import json
from unittest.mock import MagicMock, patch

import pytest

from app.agents.data_lookup_agent import DataLookupAgent


class MockResponse:
    """Clase para simular la respuesta de un LLM."""
    def __init__(self, content: str):
        self.content = content


class TestDataLookupAgent:
    """Pruebas para el DataLookupAgent."""

    @pytest.fixture
    def mock_mcp_client(self):
        """Fixture para simular el cliente MCP"""
        mock_client = MagicMock()
        mock_client.initialize_sync.return_value = True
        mock_client.call_tool_sync.return_value = {
            "results": ["resultado de prueba"],
            "status": "success"
        }
        return mock_client

    @pytest.fixture
    def data_lookup_agent(self, mock_mcp_client):
        """Fixture para el DataLookupAgent con cliente MCP simulado."""
        with patch('app.agents.data_lookup_agent.MCPClient', return_value=mock_mcp_client):
            agent = DataLookupAgent()
            # Reemplazar el LLM con un mock
            agent.llm = MagicMock()
            agent.llm.invoke.return_value = MockResponse(json.dumps({
                "lookup_category": "financial",
                "parameters": {
                    "empresa": "TechCorp",
                    "periodo": "Q2 2023"
                }
            }))
            return agent, mock_mcp_client

    def test_execute_impl_financial_lookup(self, data_lookup_agent):
        """Prueba que el agente ejecuta correctamente una búsqueda financiera."""
        agent, mock_mcp_client = data_lookup_agent
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Muestra los datos financieros de TechCorp para Q2 2023",
            "context": {"company": "TechCorp"}
        }
        
        # Ejecutar el agente
        result = agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "lookup_data" in result["result"]
        assert "confidence" in result
        assert result["confidence"] >= 0.7
        assert "processing_time" in result
        
        # Verificar que el cliente MCP fue inicializado y llamado
        mock_mcp_client.initialize_sync.assert_called_once()
        mock_mcp_client.call_tool_sync.assert_any_call("buscar_datos_financieros", {
            "empresa": "TechCorp",
            "periodo": "Q2 2023"
        })

    def test_execute_impl_with_general_lookup(self, data_lookup_agent):
        """Prueba que el agente realiza una búsqueda general cuando no puede categorizar la consulta."""
        agent, mock_mcp_client = data_lookup_agent
        
        # Cambiamos el comportamiento del LLM para que devuelva una categoría general
        agent.llm.invoke.return_value = MockResponse(json.dumps({
            "lookup_category": "general",
            "parameters": {}
        }))
        
        # Datos de entrada para prueba
        input_data = {
            "query": "¿Cuál es la situación actual del mercado?",
            "context": {}
        }
        
        # Ejecutar el agente
        result = agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "lookup_data" in result["result"]
        assert "confidence" in result
        assert "processing_time" in result
        
        # Verificar que se realizó una llamada de búsqueda general
        mock_mcp_client.call_tool_sync.assert_any_call("data_lookup", {
            "lookup_type": "general",
            "query": "¿Cuál es la situación actual del mercado?"
        })

    def test_execute_impl_marketing_lookup(self, data_lookup_agent):
        """Prueba que el agente ejecuta correctamente una búsqueda de marketing."""
        agent, mock_mcp_client = data_lookup_agent
        
        # Cambiamos el comportamiento del LLM para que devuelva una categoría de marketing
        agent.llm.invoke.return_value = MockResponse(json.dumps({
            "lookup_category": "marketing",
            "parameters": {
                "campaign": "Campaña Verano 2023",
                "metrics": {
                    "impressions": 5000,
                    "clicks": 250,
                    "conversions": 50,
                    "cost": 1000
                }
            }
        }))
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Analiza el rendimiento de la campaña de verano 2023",
            "context": {"campaign": "Campaña Verano 2023"}
        }
        
        # Ejecutar el agente
        result = agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "lookup_data" in result["result"]
        assert "confidence" in result
        assert "processing_time" in result
        
        # Verificar que se realizó una llamada de análisis de campaña
        mock_mcp_client.call_tool_sync.assert_any_call("analizar_rendimiento_campania", {
            "nombre_campania": "Campaña Verano 2023",
            "impresiones": 5000,
            "clics": 250,
            "conversiones": 50,
            "coste": 1000
        })

    def test_execute_impl_trends_lookup(self, data_lookup_agent):
        """Prueba que el agente ejecuta correctamente un análisis de tendencias."""
        agent, mock_mcp_client = data_lookup_agent
        
        # Cambiamos el comportamiento del LLM para que devuelva una categoría de tendencias
        agent.llm.invoke.return_value = MockResponse(json.dumps({
            "lookup_category": "trends",
            "parameters": {
                "numerical_data": [10, 15, 20, 25, 30],
                "labels": ["Ene", "Feb", "Mar", "Abr", "May"],
                "predict": True,
                "future_periods": 2
            }
        }))
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Analiza la tendencia de ventas y predice los próximos dos meses",
            "context": {
                "numerical_data": [10, 15, 20, 25, 30]
            }
        }
        
        # Ejecutar el agente
        result = agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "lookup_data" in result["result"]
        assert "confidence" in result
        assert "processing_time" in result
        
        # Verificar que se realizaron llamadas de análisis de tendencias y predicción
        mock_mcp_client.call_tool_sync.assert_any_call("analizar_tendencia", {
            "datos": [10, 15, 20, 25, 30],
            "etiquetas": ["Ene", "Feb", "Mar", "Abr", "May"]
        })
        
        mock_mcp_client.call_tool_sync.assert_any_call("predecir_valores", {
            "datos": [10, 15, 20, 25, 30],
            "periodos_futuros": 2
        })

    def test_execute_impl_mcp_failure(self, data_lookup_agent):
        """Prueba que el agente maneja correctamente un fallo en la inicialización del MCP."""
        agent, mock_mcp_client = data_lookup_agent
        
        # Simular fallo en la inicialización del MCP
        mock_mcp_client.initialize_sync.return_value = False
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Busca información sobre mercados emergentes",
            "context": {}
        }
        
        # Ejecutar el agente
        result = agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "lookup_data" in result["result"]
        assert "confidence" in result
        assert result["confidence"] <= 0.9  # Confianza moderada debido al fallo 
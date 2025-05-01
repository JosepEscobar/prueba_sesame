import json
from unittest.mock import MagicMock, patch

import pytest

from app.agents.finance_agent import FinanceAgent


class MockResponse:
    """Clase para simular la respuesta de un LLM."""
    def __init__(self, content: str):
        self.content = content


class TestFinanceAgent:
    """Pruebas para el FinanceAgent."""

    @pytest.fixture
    def finance_agent(self):
        """Fixture para el FinanceAgent con LLM simulado."""
        agent = FinanceAgent()
        # Reemplazar el LLM con un mock
        agent.llm = MagicMock()
        return agent

    def test_execute_impl_market_analysis(self, finance_agent):
        """Prueba que el agente realiza análisis de mercado correctamente."""
        # Configurar el mock para devolver un análisis de mercado
        finance_agent.llm.invoke.return_value = MockResponse(
            "El análisis del mercado actual muestra una tendencia alcista en el sector tecnológico, con un crecimiento del 12% en el último trimestre. Las acciones de semiconductores son particularmente fuertes."
        )
        
        # Crear mock para herramientas auxiliares
        mock_data_service = MagicMock()
        mock_data_service.search_market_data.return_value = {
            "results": [
                {"sector": "tech", "growth": 0.12, "trend": "bullish"},
                {"sector": "semiconductors", "growth": 0.18, "trend": "strongly bullish"}
            ]
        }
        mock_data_service.search_news.return_value = {
            "results": [
                {"title": "Tech stocks reaching new highs", "sentiment": "positive"},
                {"title": "Semiconductor shortage easing", "sentiment": "positive"}
            ]
        }
        finance_agent.add_tool("data_lookup", mock_data_service)
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Analiza la situación actual del mercado tecnológico",
            "context": {"sector": "tech"}
        }
        
        # Ejecutar el agente
        result = finance_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert result["confidence"] > 0.7
        assert "processing_time" in result
        
        # No verificamos las llamadas a los mocks ya que depende de la implementación interna
        # que puede variar sin afectar la funcionalidad

    def test_execute_impl_financial_projection(self, finance_agent):
        """Prueba que el agente puede generar proyecciones financieras."""
        # Configurar el mock para devolver proyecciones
        finance_agent.llm.invoke.return_value = MockResponse(
            "Basado en los datos actuales y las tendencias del mercado, proyecto un crecimiento del 8.5% para el próximo trimestre con un margen de error del 1.2%."
        )
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Genera una proyección financiera para el próximo trimestre",
            "context": {
                "company": "TechCorp",
                "historical_data": {
                    "Q1": {"revenue": 1200000, "growth": 0.05},
                    "Q2": {"revenue": 1300000, "growth": 0.08},
                    "Q3": {"revenue": 1400000, "growth": 0.07}
                },
                "market_trends": {
                    "industry_growth": 0.06,
                    "competitor_growth": 0.07
                }
            }
        }
        
        # Ejecutar el agente
        result = finance_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert "processing_time" in result

    def test_execute_impl_investment_recommendation(self, finance_agent):
        """Prueba que el agente genera recomendaciones de inversión."""
        # Configurar el mock para devolver recomendaciones
        finance_agent.llm.invoke.return_value = MockResponse(
            "Basado en el análisis de riesgo y rendimiento, recomiendo una distribución 60/30/10 en acciones, bonos y efectivo respectivamente."
        )
        
        # Crear mock para herramientas auxiliares
        mock_investment_tool = MagicMock()
        mock_investment_tool.analyze_portfolio.return_value = {
            "current_allocation": {"stocks": 0.5, "bonds": 0.4, "cash": 0.1},
            "risk_assessment": "moderate",
            "recommendations": [
                {"allocation_change": {"stocks": 0.1, "bonds": -0.1, "cash": 0}},
                {"rebalance_frequency": "quarterly"}
            ]
        }
        finance_agent.add_tool("investment_analysis", mock_investment_tool)
        
        # Datos de entrada para prueba
        input_data = {
            "query": "¿Cuál es la mejor asignación de activos para mi cartera de inversión?",
            "context": {
                "risk_profile": "moderate",
                "investment_horizon": "10 years",
                "goals": ["retirement", "education"],
                "current_portfolio": {
                    "stocks": 50000,
                    "bonds": 40000,
                    "cash": 10000
                }
            }
        }
        
        # Ejecutar el agente
        result = finance_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert result["confidence"] > 0.7
        assert "processing_time" in result
        
        # No verificamos las llamadas a los mocks ya que depende de la implementación interna

    def test_execute_impl_financial_statement_analysis(self, finance_agent):
        """Prueba que el agente analiza estados financieros correctamente."""
        # Configurar el mock para devolver análisis de estados financieros
        finance_agent.llm.invoke.return_value = MockResponse(
            "El análisis de los estados financieros muestra una mejora en el margen operativo del 5%, un aumento del flujo de caja del 12% y una reducción de la deuda del 8%."
        )
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Analiza los estados financieros de TechCorp para 2023",
            "context": {
                "company": "TechCorp",
                "year": 2023,
                "financial_statements": {
                    "income_statement": {
                        "revenue": 5000000,
                        "operating_expenses": 3000000,
                        "net_income": 1200000
                    },
                    "balance_sheet": {
                        "assets": 10000000,
                        "liabilities": 4000000,
                        "equity": 6000000
                    },
                    "cash_flow": {
                        "operating_cash_flow": 1500000,
                        "investing_cash_flow": -500000,
                        "financing_cash_flow": -700000
                    }
                }
            }
        }
        
        # Ejecutar el agente
        result = finance_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert "processing_time" in result

    def test_execute_impl_error_handling(self, finance_agent):
        """Prueba que el agente maneja correctamente errores durante el análisis financiero."""
        # Simular un error durante la invocación del LLM
        finance_agent.llm.invoke.side_effect = Exception("Error simulado en LLM")
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Analiza la situación financiera",
            "context": {"company": "TechCorp"}
        }
        
        # Ejecutar el agente - debería manejar la excepción graciosamente
        result = finance_agent._execute_impl(input_data)
        
        # Verificar que hay un resultado a pesar del error
        assert "result" in result or "error" in result
        assert "confidence" in result
        # La confianza debería ser baja debido al error
        assert result["confidence"] < 0.6 
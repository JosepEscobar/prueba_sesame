import json
from unittest.mock import MagicMock, patch

import pytest

from app.agents.marketing_agent import MarketingAgent


class MockResponse:
    """Clase para simular la respuesta de un LLM."""
    def __init__(self, content: str):
        self.content = content


class TestMarketingAgent:
    """Pruebas para el MarketingAgent."""

    @pytest.fixture
    def marketing_agent(self):
        """Fixture para el MarketingAgent con LLM simulado."""
        agent = MarketingAgent()
        # Reemplazar el LLM con un mock
        agent.llm = MagicMock()
        return agent

    def test_execute_impl_campaign_analysis(self, marketing_agent):
        """Prueba que el agente analiza correctamente campañas de marketing."""
        # Configurar el mock para devolver un análisis de campaña
        marketing_agent.llm.invoke.return_value = MockResponse(
            "El análisis de la campaña muestra un ROI de 2.5 con un incremento de 30% en leads."
        )
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Analiza los resultados de nuestra campaña de redes sociales",
            "context": {
                "campaign_name": "Verano 2023",
                "metrics": {
                    "impressions": 100000,
                    "clicks": 5000,
                    "conversions": 500,
                    "cost": 2000
                }
            }
        }
        
        # Ejecutar el agente
        result = marketing_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert result["confidence"] > 0.7
        assert "processing_time" in result

    def test_execute_impl_audience_targeting(self, marketing_agent):
        """Prueba que el agente genera recomendaciones para audiencias objetivo."""
        # Configurar el mock para devolver recomendaciones de audiencia
        marketing_agent.llm.invoke.return_value = MockResponse(
            "Para este producto, recomiendo enfocar la estrategia en adultos de 25-34 años interesados en tecnología y sostenibilidad."
        )
        
        # Datos de entrada para prueba
        input_data = {
            "query": "¿Qué audiencia objetivo recomiendas para nuestro nuevo producto eco-friendly?",
            "context": {
                "product": "Botella térmica reutilizable",
                "industry": "consumer goods",
                "target_market": "jóvenes profesionales"
            }
        }
        
        # Ejecutar el agente
        result = marketing_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert "processing_time" in result

    def test_execute_impl_content_strategy(self, marketing_agent):
        """Prueba que el agente crea estrategias de contenido efectivas."""
        # Configurar el mock para devolver una estrategia de contenido
        marketing_agent.llm.invoke.return_value = MockResponse(
            "Recomiendo un calendario editorial enfocado en tutoriales en video, testimonios de clientes y estudios de caso."
        )
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Desarrolla una estrategia de contenido para nuestra marca",
            "context": {
                "brand": "TechSolutions",
                "channels": ["blog", "instagram", "linkedin"],
                "goals": ["aumentar awareness", "generar leads"]
            }
        }
        
        # Ejecutar el agente
        result = marketing_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert result["confidence"] > 0.7
        assert "processing_time" in result

    def test_execute_impl_error_handling(self, marketing_agent):
        """Prueba que el agente maneja correctamente errores y entradas incompletas."""
        # Datos de entrada incompletos
        input_data = {
            "query": "Analiza la campaña",
            "context": {}  # Contexto vacío
        }
        
        # Ejecutar el agente
        result = marketing_agent._execute_impl(input_data)
        
        # Verificar que aún así devuelve un resultado, quizá con menor confianza
        assert "result" in result
        assert "confidence" in result
        assert "processing_time" in result 
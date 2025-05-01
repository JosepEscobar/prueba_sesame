import json
from unittest.mock import MagicMock, patch

import pytest

from app.agents.analysis_agent import AnalysisAgent


class MockResponse:
    """Clase para simular la respuesta de un LLM."""
    def __init__(self, content: str):
        self.content = content


class TestAnalysisAgent:
    """Pruebas para el AnalysisAgent."""

    @pytest.fixture
    def analysis_agent(self):
        """Fixture para el AnalysisAgent con LLM simulado."""
        agent = AnalysisAgent()
        # Reemplazar el LLM con un mock
        agent.llm = MagicMock()
        return agent

    def test_execute_impl_text_analysis(self, analysis_agent):
        """Prueba que el agente realiza un análisis detallado de texto."""
        # Configurar el mock para devolver un análisis de texto
        analysis_agent.llm.invoke.return_value = MockResponse(
            "El texto presenta una argumentación clara con tres puntos principales. La estructura es coherente y utiliza un tono formal."
        )
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Analiza este documento de texto",
            "context": {
                "document": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
                "type": "text"
            }
        }
        
        # Ejecutar el agente
        result = analysis_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert result["confidence"] > 0.7
        assert "processing_time" in result

    def test_execute_impl_data_analysis(self, analysis_agent):
        """Prueba que el agente realiza un análisis de datos numéricos."""
        # Configurar el mock para devolver un análisis de datos
        analysis_agent.llm.invoke.return_value = MockResponse(
            "Los datos muestran una tendencia alcista con un incremento promedio del 5.3% mensual. Se observa una estacionalidad clara en los trimestres Q2 y Q4."
        )
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Analiza estos datos de ventas",
            "context": {
                "data": [10, 12, 15, 14, 18, 22, 24, 20, 25, 28, 32, 30],
                "labels": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
                "type": "numeric"
            }
        }
        
        # Ejecutar el agente
        result = analysis_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert "processing_time" in result

    def test_execute_impl_mixed_content_analysis(self, analysis_agent):
        """Prueba que el agente analiza contenido mixto (texto y datos)."""
        # Configurar el mock para devolver un análisis mixto
        analysis_agent.llm.invoke.return_value = MockResponse(
            "El informe muestra una correlación entre la narrativa textual y los datos cuantitativos. Los puntos destacados en el texto están respaldados por las métricas presentadas."
        )
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Analiza el informe trimestral y sus datos asociados",
            "context": {
                "text": "El trimestre Q3 ha mostrado un crecimiento significativo en el sector de tecnología, con un incremento notable en la adopción de soluciones cloud.",
                "data": {
                    "cloud_adoption": [15, 18, 22, 27],
                    "revenue_growth": [5, 7, 8, 12]
                },
                "type": "mixed"
            }
        }
        
        # Ejecutar el agente
        result = analysis_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert result["confidence"] > 0.7
        assert "processing_time" in result

    def test_execute_impl_with_specific_instructions(self, analysis_agent):
        """Prueba que el agente sigue instrucciones específicas para el análisis."""
        # Configurar el mock para devolver un análisis específico
        analysis_agent.llm.invoke.return_value = MockResponse(
            "Análisis FODA: Fortalezas - amplia base de clientes, tecnología propietaria. Debilidades - alto costo operativo. Oportunidades - mercados emergentes. Amenazas - nuevos competidores con precios agresivos."
        )
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Realiza un análisis FODA de nuestra empresa",
            "context": {
                "company_data": {
                    "name": "TechCorp",
                    "employees": 500,
                    "revenue": 10000000,
                    "market_share": 0.15,
                    "competitors": ["CompA", "CompB", "CompC"]
                },
                "instructions": "Enfócate en aspectos de competitividad y expansión internacional"
            }
        }
        
        # Ejecutar el agente
        result = analysis_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert "processing_time" in result

    def test_execute_impl_error_handling(self, analysis_agent):
        """Prueba que el agente maneja correctamente errores durante el análisis."""
        # Simular un error durante la invocación del LLM
        analysis_agent.llm.invoke.side_effect = Exception("Error simulado en LLM")
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Analiza estos datos",
            "context": {"data": [1, 2, 3]}
        }
        
        # Ejecutar el agente - debería manejar la excepción graciosamente
        result = analysis_agent._execute_impl(input_data)
        
        # Verificar que hay un resultado a pesar del error
        assert "result" in result
        assert "confidence" in result
        # La confianza debería ser baja debido al error
        assert result["confidence"] < 0.6 
import json
from unittest.mock import MagicMock, patch

import pytest

from app.agents.summary_agent import SummaryAgent


class MockResponse:
    """Clase para simular la respuesta de un LLM."""
    def __init__(self, content: str):
        self.content = content


class TestSummaryAgent:
    """Pruebas para el SummaryAgent."""

    @pytest.fixture
    def summary_agent(self):
        """Fixture para el SummaryAgent con LLM simulado."""
        agent = SummaryAgent()
        # Reemplazar el LLM con un mock
        agent.llm = MagicMock()
        return agent

    def test_execute_impl_short_text_summary(self, summary_agent):
        """Prueba que el agente resume correctamente textos cortos."""
        # Configurar el mock para devolver un resumen
        summary_agent.llm.invoke.return_value = MockResponse(
            "El texto describe el funcionamiento básico de los mercados financieros y su impacto en la economía global."
        )
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Resume este texto sobre mercados financieros",
            "context": {
                "text": "Los mercados financieros son espacios donde se intercambian activos financieros. Las empresas utilizan estos mercados para financiar sus operaciones. Los inversores participan para generar rendimientos. La liquidez y eficiencia son características clave de estos mercados. El comportamiento de los mercados puede afectar a la economía global.",
                "max_length": 30
            }
        }
        
        # Ejecutar el agente
        result = summary_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert result["confidence"] > 0.7
        assert "processing_time" in result

    def test_execute_impl_long_document_summary(self, summary_agent):
        """Prueba que el agente resume correctamente documentos largos."""
        # Configurar el mock para devolver un resumen de documento largo
        summary_agent.llm.invoke.return_value = MockResponse(
            "El informe anual muestra un crecimiento del 12% en ingresos, expansión en tres nuevos mercados, y un aumento de la plantilla del 8%. Los desafíos principales fueron la inflación y problemas en la cadena de suministro."
        )
        
        # Crear un documento largo para la prueba
        long_doc = " ".join(["Lorem ipsum dolor sit amet, consectetur adipiscing elit."] * 50)
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Resume el informe anual de 2023",
            "context": {
                "document": long_doc,
                "type": "annual_report",
                "year": 2023,
                "max_length": 50
            }
        }
        
        # Ejecutar el agente
        result = summary_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert "processing_time" in result

    def test_execute_impl_data_summary(self, summary_agent):
        """Prueba que el agente resume correctamente datos numéricos."""
        # Configurar el mock para devolver un resumen de datos
        summary_agent.llm.invoke.return_value = MockResponse(
            "Los datos financieros muestran un crecimiento constante en los últimos 4 trimestres, con un aumento total anual del 15%. El segundo trimestre fue el de mayor rendimiento."
        )
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Resume los resultados financieros trimestrales",
            "context": {
                "data": {
                    "Q1": {"revenue": 1200000, "expenses": 900000, "profit": 300000},
                    "Q2": {"revenue": 1500000, "expenses": 1000000, "profit": 500000},
                    "Q3": {"revenue": 1400000, "expenses": 950000, "profit": 450000},
                    "Q4": {"revenue": 1600000, "expenses": 1100000, "profit": 500000}
                },
                "focus": "trends"
            }
        }
        
        # Ejecutar el agente
        result = summary_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert result["confidence"] > 0.7
        assert "processing_time" in result

    def test_execute_impl_meeting_summary(self, summary_agent):
        """Prueba que el agente resume correctamente notas de reuniones."""
        # Configurar el mock para devolver un resumen de reunión
        summary_agent.llm.invoke.return_value = MockResponse(
            "En la reunión se discutieron 3 puntos principales: 1) Nuevas metas de ventas para Q4, 2) Estrategia de marketing para el nuevo producto, 3) Mejoras en la atención al cliente. Se acordó revisar avances en dos semanas."
        )
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Resume las notas de la reunión de estrategia",
            "context": {
                "meeting_notes": """
                Fecha: 15/10/2023
                Asistentes: Juan, María, Carlos, Laura, Ahmed
                
                Puntos discutidos:
                1. Juan presentó las cifras actuales de ventas y propuso aumentar las metas para Q4 en un 15%.
                2. María habló sobre la estrategia de marketing para el lanzamiento del nuevo producto en noviembre.
                3. Carlos mencionó problemas recientes con la atención al cliente y propuso soluciones.
                4. Laura compartió feedback de clientes sobre el servicio.
                5. Ahmed presentó métricas de satisfacción de clientes.
                
                Acciones:
                - Revisar cifras de ventas en detalle (Juan)
                - Finalizar plan de marketing (María)
                - Implementar mejoras en atención al cliente (Carlos)
                - Reunión de seguimiento en dos semanas
                """,
                "extract_key_points": True
            }
        }
        
        # Ejecutar el agente
        result = summary_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert "processing_time" in result

    def test_execute_impl_error_handling(self, summary_agent):
        """Prueba que el agente maneja correctamente errores durante el resumen."""
        # Simular un error durante la invocación del LLM
        summary_agent.llm.invoke.side_effect = Exception("Error simulado en LLM")
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Resume este texto",
            "context": {"text": "Contenido a resumir"}
        }
        
        # Ejecutar el agente - debería manejar la excepción graciosamente
        result = summary_agent._execute_impl(input_data)
        
        # Verificar que hay un mensaje de error cuando falla
        assert "error" in result
        assert "Error simulado en LLM" in result["error"]
        assert "confidence" in result
        # La confianza debería ser baja debido al error
        assert result["confidence"] < 0.6 
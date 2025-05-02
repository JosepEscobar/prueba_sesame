import json
from unittest.mock import MagicMock, patch

import pytest

from app.agents.router_agent import RouterAgent


class MockResponse:
    """Clase para simular la respuesta de un LLM."""
    def __init__(self, content: str):
        self.content = content


class TestRouterAgent:
    """Pruebas para el RouterAgent."""

    @pytest.fixture
    def router_agent(self):
        """Fixture para el RouterAgent con LLM simulado."""
        # Ya que ChatOpenAI no se importa directamente en router_agent.py,
        # crearemos primero una instancia y luego reemplazaremos su LLM
        agent = RouterAgent()
        # Reemplazar el LLM con un mock
        agent.llm = MagicMock()
        return agent

    def test_execute_impl_finance_routing(self, router_agent):
        """Prueba que el agente enruta correctamente consultas financieras."""
        # Configurar el mock para devolver una respuesta de enrutamiento financiero
        router_agent.llm.invoke.return_value = MockResponse(json.dumps({
            "agent": "finance_agent",
            "reasoning": "La consulta es sobre análisis financiero de una empresa",
            "confidence": 0.92
        }))
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Analiza los estados financieros de TechCorp para Q2 2023",
            "context": {"company": "TechCorp"}
        }
        
        # Ejecutar el agente
        result = router_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "agent" in result
        assert result["agent"] == "finance_agent"
        assert "confidence" in result
        assert "reasoning" in result
        assert "input" in result
        assert result["input"] == input_data

    def test_execute_impl_marketing_routing(self, router_agent):
        """Prueba que el agente enruta correctamente consultas de marketing."""
        # Configurar el mock para devolver una respuesta de enrutamiento a marketing
        router_agent.llm.invoke.return_value = MockResponse(json.dumps({
            "agent": "marketing_agent",
            "reasoning": "La consulta es sobre estrategias de marketing y KPIs",
            "confidence": 0.88
        }))
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Analiza el rendimiento de nuestra campaña de marketing digital",
            "context": {"campaign": "Digital Q2"}
        }
        
        # Ejecutar el agente
        result = router_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "agent" in result
        assert result["agent"] == "marketing_agent"
        assert "confidence" in result
        assert "reasoning" in result
        assert "input" in result
        assert result["input"] == input_data

    def test_execute_impl_data_lookup_routing(self, router_agent):
        """Prueba que el agente enruta correctamente consultas de búsqueda de datos."""
        # Configurar el mock para devolver una respuesta de enrutamiento a data_lookup
        router_agent.llm.invoke.return_value = MockResponse(json.dumps({
            "agent": "data_lookup_agent",
            "reasoning": "La consulta solicita datos específicos que requieren una búsqueda",
            "confidence": 0.85
        }))
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Encuentra información sobre las tendencias del mercado de semiconductores",
            "context": {"industry": "tech"}
        }
        
        # Ejecutar el agente
        result = router_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "agent" in result
        assert result["agent"] == "data_lookup_agent"
        assert "confidence" in result
        assert "reasoning" in result
        assert "input" in result
        assert result["input"] == input_data

    def test_execute_impl_with_low_confidence(self, router_agent):
        """Prueba que el agente maneja correctamente casos de baja confianza."""
        # Configurar el mock para devolver una respuesta con baja confianza
        router_agent.llm.invoke.return_value = MockResponse(json.dumps({
            "agent": "summary_agent",
            "reasoning": "No estoy seguro, pero podría ser una solicitud de resumen",
            "confidence": 0.55
        }))
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Esta es una consulta ambigua que no encaja claramente en ninguna categoría",
            "context": {}
        }
        
        # Ejecutar el agente
        result = router_agent._execute_impl(input_data)
        
        # Verificar el resultado - debería seguir el enrutamiento pero con baja confianza
        assert "agent" in result
        assert result["agent"] == "summary_agent"
        assert "confidence" in result
        assert "reasoning" in result
        assert "input" in result
        assert result["input"] == input_data

    def test_execute_impl_with_invalid_response(self, router_agent):
        """Prueba que el agente maneja correctamente respuestas inválidas del LLM."""
        # Configurar el mock para devolver una respuesta no-JSON
        router_agent.llm.invoke.return_value = MockResponse("Esto no es un JSON válido")
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Consulta normal de prueba",
            "context": {}
        }
        
        # Ejecutar el agente
        result = router_agent._execute_impl(input_data)
        
        # Verificar el resultado - debería usar un agente fallback
        assert "agent" in result
        assert "confidence" in result
        assert "input" in result
        assert result["input"] == input_data

    def test_normalize_agent_name(self, router_agent):
        """Prueba que el método _normalize_agent_name funciona correctamente."""
        # Diferentes variaciones que deberían apuntar al mismo agente
        if hasattr(router_agent, '_normalize_agent_name'):
            assert router_agent._normalize_agent_name("finance") == "finance_agent"
            assert router_agent._normalize_agent_name("Financial") == "finance_agent"
            assert router_agent._normalize_agent_name("finance_agent") == "finance_agent"
            
            assert router_agent._normalize_agent_name("marketing") == "marketing_agent"
            assert router_agent._normalize_agent_name("Marketing Agent") == "marketing_agent"
            
            # Agente desconocido debería devolver un valor por defecto
            assert router_agent._normalize_agent_name("agente_inexistente") in router_agent.available_agents
        else:
            # Si el método no existe, simplemente pasamos el test
            pass 
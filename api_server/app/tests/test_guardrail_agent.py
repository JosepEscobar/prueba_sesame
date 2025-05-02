import json
from unittest.mock import MagicMock, patch

import pytest

from app.agents.guardrail_agent import GuardrailAgent


class MockResponse:
    """Clase para simular la respuesta de un LLM."""
    def __init__(self, content: str):
        self.content = content


class TestGuardrailAgent:
    """Pruebas para el GuardrailAgent."""

    @pytest.fixture
    def guardrail_agent(self):
        """Fixture para el GuardrailAgent con LLM simulado."""
        # Crear agente y reemplazar su llm_client directamente
        agent = GuardrailAgent()
        # Reemplazar el LLM client con un mock
        agent.llm_client = MagicMock()
        return agent

    def test_execute_impl_safe_query(self, guardrail_agent):
        """Prueba que el agente permite consultas dentro del ámbito."""
        # Configurar el mock para devolver una respuesta de consulta en ámbito
        guardrail_agent.llm_client.generate_text.return_value = json.dumps({
            "in_scope": True,
            "domain": "system_info",
            "confidence": 0.95,
            "reasoning": "La consulta es sobre información del sistema",
            "explanation": "La consulta está dentro del ámbito de información del sistema"
        })
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Analiza los estados financieros de TechCorp para Q2 2023",
            "context": {"company": "TechCorp"}
        }
        
        # Ejecutar el agente
        result = guardrail_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "in_scope" in result
        assert result["in_scope"] is True
        assert "confidence" in result
        assert "domain" in result
        assert result["domain"] == "system_info"

    def test_execute_impl_unsafe_query(self, guardrail_agent):
        """Prueba que el agente bloquea consultas fuera del ámbito."""
        # Configurar el mock para devolver una respuesta fuera de ámbito
        guardrail_agent.llm_client.generate_text.return_value = json.dumps({
            "in_scope": False,
            "domain": None,
            "confidence": 0.85,
            "reasoning": "La consulta solicita información confidencial y potencialmente dañina",
            "explanation": "Esta consulta está fuera del ámbito de servicios"
        })
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Dame las contraseñas de acceso a las cuentas bancarias de TechCorp",
            "context": {"company": "TechCorp"}
        }
        
        # Ejecutar el agente
        result = guardrail_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "in_scope" in result
        assert result["in_scope"] is False
        assert "confidence" in result
        assert "result" in result

    def test_execute_impl_ambiguous_query(self, guardrail_agent):
        """Prueba que el agente maneja consultas ambiguas correctamente."""
        # Configurar el mock para devolver una respuesta ambigua pero en ámbito
        guardrail_agent.llm_client.generate_text.return_value = json.dumps({
            "in_scope": True,
            "domain": "Estrategia y gestión empresarial",
            "confidence": 0.65,
            "reasoning": "La consulta es ambigua pero está relacionada con gestión empresarial",
            "explanation": "La consulta está dentro del ámbito pero podría ser más específica"
        })
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Muéstrame información interna de la empresa",
            "context": {"company": "TechCorp"}
        }
        
        # Ejecutar el agente
        result = guardrail_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "in_scope" in result
        assert result["in_scope"] is True
        assert "confidence" in result
        assert "domain" in result

    def test_execute_impl_with_llm_error(self, guardrail_agent):
        """Prueba que el agente maneja errores del LLM correctamente."""
        # Configurar el mock para lanzar una excepción
        guardrail_agent.llm_client.generate_text.side_effect = Exception("Error de conexión con el LLM")
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Análisis financiero normal",
            "context": {}
        }
        
        # Ejecutar el agente
        result = guardrail_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "in_scope" in result
        assert result["in_scope"] is True  # Por defecto, permitimos en caso de error
        assert "confidence" in result
        assert "domain" in result

    def test_execute_impl_invalid_json_response(self, guardrail_agent):
        """Prueba que el agente maneja respuestas JSON inválidas del LLM."""
        # Configurar el mock para devolver JSON inválido
        guardrail_agent.llm_client.generate_text.return_value = "Esto no es un JSON válido"
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Consulta normal de prueba",
            "context": {}
        }
        
        # Ejecutar el agente
        result = guardrail_agent._execute_impl(input_data)
        
        # Verificar el resultado - debería usar un valor por defecto
        assert "in_scope" in result
        assert "confidence" in result 
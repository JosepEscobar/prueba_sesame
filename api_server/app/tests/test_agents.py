import json
from unittest.mock import MagicMock

import pytest

from app.agents.action_agent import ActionAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.marketing_agent import MarketingAgent
from app.agents.router_agent import RouterAgent
from app.agents.summary_agent import SummaryAgent


class MockResponse:
    """Clase para simular la respuesta de un LLM."""
    def __init__(self, content: str):
        self.content = content

class MockLLM:
    """Clase para simular un LLM."""
    def __init__(self, response_content: str = ""):
        self.response_content = response_content
        self.invoke_count = 0
        self.last_prompt = None

    def invoke(self, prompt: str | dict | list, **kwargs):
        """Simula la invocación de un LLM."""
        self.invoke_count += 1
        self.last_prompt = prompt
        return MockResponse(self.response_content)

    def get_invoke_count(self):
        """Retorna el número de veces que se ha llamado a invoke."""
        return self.invoke_count

    def assert_called_once(self):
        """Verifica que invoke haya sido llamado exactamente una vez."""
        if self.invoke_count != 1:
            raise AssertionError(f"Expected 'invoke' to have been called once. Called {self.invoke_count} times.")

@pytest.fixture
def mock_llm():
    """Mock para simular respuestas del LLM."""
    return MockLLM(json.dumps({
        "agent": "finance_agent",
        "reasoning": "La consulta es sobre finanzas",
        "confidence": 0.85
    }))

@pytest.fixture
def mock_llm_response():
    """Mock para simular una respuesta simple del LLM."""
    return MockLLM("Esta es una respuesta de prueba")

@pytest.fixture
def router_agent_with_mock(monkeypatch):
    """Fixture para el RouterAgent con LLM simulado."""
    mock = MockLLM(json.dumps({
        "agent": "finance_agent",
        "reasoning": "La consulta es sobre finanzas",
        "confidence": 0.85
    }))
    monkeypatch.setattr("app.agents.router_agent.llm", mock)
    agent = RouterAgent(model="test-model")
    return agent, mock

@pytest.fixture
def summary_agent_with_mock(monkeypatch):
    """Fixture para el SummaryAgent con LLM simulado."""
    mock = MockLLM("Este es un resumen de prueba")
    monkeypatch.setattr("app.agents.summary_agent.llm", mock)
    agent = SummaryAgent(model="test-model")
    return agent, mock

@pytest.fixture
def analysis_agent_with_mock(monkeypatch):
    """Fixture para el AnalysisAgent con LLM simulado."""
    mock = MockLLM("Este es un análisis detallado del documento...")
    monkeypatch.setattr("app.agents.analysis_agent.llm", mock)
    agent = AnalysisAgent(model="test-model")
    return agent, mock

@pytest.fixture
def action_agent_with_mock(monkeypatch):
    """Fixture para el ActionAgent con LLM simulado."""
    mock = MockLLM("Acción completada: se creó un reporte financiero")
    monkeypatch.setattr("app.agents.action_agent.llm", mock)
    agent = ActionAgent(model="test-model")
    return agent, mock

@pytest.fixture
def finance_agent(monkeypatch):
    """Fixture para el FinanceAgent con LLM simulado."""
    mock_llm = MockLLM("Este es un análisis financiero de prueba")
    agent = FinanceAgent()
    agent.llm = mock_llm
    return agent

@pytest.fixture
def marketing_agent(monkeypatch):
    """Fixture para el MarketingAgent con LLM simulado."""
    mock_llm = MockLLM("Este es un análisis de marketing de prueba")
    agent = MarketingAgent()
    agent.llm = mock_llm
    return agent

def test_router_agent_extract_decision():
    """Test que el RouterAgent extrae correctamente la decisión del agente."""
    agent = RouterAgent(model="test-model")
    json_response = '{"agent": "finance", "reasoning": "La consulta es sobre finanzas", "confidence": 0.85}'
    decision = agent._extract_agent_decision(json_response)

    assert decision["agent"] == "finance_agent"
    assert decision["confidence"] == 0.85
    assert "reasoning" in decision

def test_router_agent_fallback():
    """Test que el RouterAgent maneja correctamente respuestas inválidas."""
    # Respuesta inválida (no JSON)
    agent = RouterAgent(model="test-model")
    invalid_response = "No soy un JSON válido"
    decision = agent._extract_agent_decision(invalid_response)

    assert "agent" in decision
    assert decision["confidence"] <= 0.6  # Confianza reducida para fallback

def test_router_agent_execute(router_agent_with_mock):
    """Test que el RouterAgent ejecuta correctamente."""
    router_agent, mock = router_agent_with_mock
    # Crear una consulta de prueba
    input_data = {
        "query": "¿Cuáles son las mejores estrategias de inversión para 2023?",
        "context": {"industry": "fintech"}
    }

    # Ejecutar el agente
    result = router_agent._execute_impl(input_data)

    # Verificar el resultado
    assert "agent" in result
    assert "confidence" in result
    assert "input" in result
    assert result["input"] == input_data
    assert mock.get_invoke_count() > 0

def test_summary_agent_execute(summary_agent_with_mock):
    """Test que el SummaryAgent ejecuta correctamente."""
    summary_agent, mock = summary_agent_with_mock

    # Crear una consulta de prueba
    input_data = {
        "query": "Resume esta información",
        "context": "Información detallada que necesita ser resumida..."
    }

    # Ejecutar el agente
    result = summary_agent._execute_impl(input_data)

    # Verificar el resultado
    assert "result" in result
    assert result["result"] == "Este es un resumen de prueba"
    assert "confidence" in result
    assert result["confidence"] == 0.85
    assert mock.get_invoke_count() > 0

def test_finance_agent_execute(finance_agent):
    """Test que el FinanceAgent ejecuta correctamente."""
    # Crear una consulta de prueba
    input_data = {
        "query": "Analiza el mercado financiero actual",
        "context": {"industry": "banca"}
    }

    # Crear mock para data_lookup
    mock_data_service = MagicMock()
    mock_data_service.search_market_data.return_value = {"results": []}
    mock_data_service.search_news.return_value = {"results": []}
    finance_agent.add_tool("data_lookup", mock_data_service)

    # Ejecutar el agente
    result = finance_agent._execute_impl(input_data)

    # Verificar el resultado
    assert "result" in result
    assert "confidence" in result
    assert "data_sources" in result

def test_marketing_agent_execute(marketing_agent):
    """Test que el MarketingAgent ejecuta correctamente."""
    # Crear una consulta de prueba
    input_data = {
        "query": "Estrategias de marketing digital para fintech",
        "context": {"target_market": "millennials"}
    }

    # Crear mock para data_lookup
    mock_data_service = MagicMock()
    mock_data_service.search_market_data.return_value = {"results": []}
    mock_data_service.search_news.return_value = {"results": []}
    marketing_agent.add_tool("data_lookup", mock_data_service)

    # Ejecutar el agente
    result = marketing_agent._execute_impl(input_data)

    # Verificar el resultado
    assert "result" in result
    assert "confidence" in result
    assert "data_sources" in result

class TestRouterAgent:
    """Pruebas para el RouterAgent."""

    def test_execute_impl(self, router_agent_with_mock):
        """Prueba del método _execute_impl de RouterAgent."""
        agent, mock = router_agent_with_mock

        # Ejecutar el agente
        result = agent.execute({"query": "Analiza este documento financiero"})

        # Verificar el resultado
        assert "agent" in result
        assert "confidence" in result
        assert "input" in result

        # Verificar que el LLM fue llamado
        assert mock.get_invoke_count() > 0

class TestAnalysisAgent:
    """Pruebas para el AnalysisAgent."""

    def test_execute_impl(self, analysis_agent_with_mock):
        """Prueba del método _execute_impl de AnalysisAgent."""
        agent, mock = analysis_agent_with_mock

        # Ejecutar el agente
        result = agent.execute({"query": "Analiza este documento"})

        # Verificar el resultado
        assert "analysis_result" in result
        assert "confidence" in result
        assert "input" in result
        assert "processing_time" in result

        # Verificar que el LLM fue llamado
        assert mock.get_invoke_count() > 0

class TestActionAgent:
    """Pruebas para el ActionAgent."""

    def test_execute_impl(self, action_agent_with_mock):
        """Prueba del método _execute_impl de ActionAgent."""
        agent, mock = action_agent_with_mock

        # Ejecutar el agente
        result = agent.execute({"query": "Crea un reporte financiero"})

        # Verificar el resultado
        assert "action_result" in result
        assert "confidence" in result
        assert "input" in result
        assert "processing_time" in result

        # Verificar que el LLM fue llamado
        assert mock.get_invoke_count() > 0

class TestSummaryAgent:
    """Pruebas para el SummaryAgent."""

    def test_execute_impl(self, summary_agent_with_mock):
        """Prueba del método _execute_impl de SummaryAgent."""
        agent, mock = summary_agent_with_mock

        # Ejecutar el agente
        result = agent.execute({"query": "Resume este documento extenso"})

        # Verificar el resultado
        assert "summary_result" in result
        assert "result" in result
        assert "confidence" in result
        assert "input" in result
        assert "processing_time" in result

        # Verificar que el LLM fue llamado
        assert mock.get_invoke_count() > 0

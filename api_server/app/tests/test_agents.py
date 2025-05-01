import json
from unittest.mock import MagicMock

import pytest

from app.agents.router_agent import RouterAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.action_agent import ActionAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.summary_agent import SummaryAgent


class MockLLM:
    """Mock de LLM para pruebas."""
    def __init__(self, response_text):
        self.response_text = response_text
        self.invoke_count = 0

    def invoke(self, prompt):
        """Simula la invocación del LLM."""
        self.invoke_count += 1
        return type('obj', (object,), {'content': self.response_text})

    def get_invoke_count(self):
        """Retorna el número de veces que se ha llamado al LLM."""
        return self.invoke_count


@pytest.fixture
def summary_agent():
    """Fixture para un SummaryAgent real."""
    return SummaryAgent()


@pytest.fixture
def analysis_agent():
    """Fixture para un AnalysisAgent real."""
    return AnalysisAgent()


@pytest.fixture
def action_agent():
    """Fixture para un ActionAgent real."""
    return ActionAgent()


@pytest.fixture
def finance_agent():
    """Fixture para un FinanceAgent real."""
    return FinanceAgent()


@pytest.fixture
def summary_agent_with_mock():
    """Fixture para el SummaryAgent con LLM simulado."""
    mock = MockLLM("Este es un resumen de prueba")
    agent = SummaryAgent()
    agent.llm = mock
    return agent, mock


@pytest.fixture
def analysis_agent_with_mock():
    """Fixture para el AnalysisAgent con LLM simulado."""
    mock = MockLLM("Este es un análisis detallado del documento...")
    agent = AnalysisAgent()
    agent.llm = mock
    return agent, mock


@pytest.fixture
def action_agent_with_mock():
    """Fixture para el ActionAgent con LLM simulado."""
    mock = MockLLM("He creado un reporte financiero basado en los datos proporcionados.")
    agent = ActionAgent()
    agent.llm = mock
    return agent, mock


def test_router_agent_basic():
    """Test de inicialización básica del RouterAgent."""
    agent = RouterAgent(model="test-model")
    assert agent.name == "router_agent"
    assert "enrutamiento" in agent.description.lower()


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


class TestAnalysisAgent:
    """Pruebas para el AnalysisAgent."""
    
    def test_execute_impl(self, analysis_agent_with_mock):
        """Prueba del método _execute_impl de AnalysisAgent."""
        agent, mock = analysis_agent_with_mock
        
        # Ejecutar el agente
        result = agent.execute({"query": "Analiza este documento"})
        
        # Verificar el resultado
        assert "result" in result


class TestActionAgent:
    """Pruebas para el ActionAgent."""
    
    def test_execute_impl(self, action_agent_with_mock):
        """Prueba del método _execute_impl de ActionAgent."""
        agent, mock = action_agent_with_mock
        
        # Ejecutar el agente
        result = agent.execute({"query": "Crea un reporte financiero"})
        
        # Verificar el resultado
        assert "result" in result or "action_result" in result
        assert "confidence" in result


class TestSummaryAgent:
    """Pruebas para el SummaryAgent."""
    
    def test_execute_impl(self, summary_agent_with_mock):
        """Prueba del método _execute_impl de SummaryAgent."""
        agent, mock = summary_agent_with_mock
        
        # Ejecutar el agente
        result = agent.execute({"query": "Resume este documento extenso"})
        
        # Verificar el resultado
        assert "result" in result

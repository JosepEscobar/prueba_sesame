import pytest
from fastapi.testclient import TestClient
import json
from app.main import app
from app.core.orchestrator import AgentOrchestrator
from unittest.mock import patch, MagicMock
from app.agents.base import BaseAgent
from app.core.orchestrator import Orchestrator
from app.agents.router_agent import RouterAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.action_agent import ActionAgent
from app.agents.summary_agent import SummaryAgent

client = TestClient(app)

class MockAgent(BaseAgent):
    """Agente simulado para pruebas."""
    
    def __init__(self, name, response=None, confidence=0.9):
        super().__init__(name=name, model="gpt-3.5-turbo")
        self.response = response or {"result": f"Respuesta de {name}"}
        self.confidence = confidence
        
    def _execute_impl(self, input_data):
        return {
            "result": self.response,
            "input": input_data,
            "confidence": self.confidence
        }

@pytest.fixture
def mock_router():
    """Fixture para crear un agente router simulado."""
    def router_response(input_data):
        # Simular decisión del router
        if "finanzas" in input_data.lower():
            decision = "FinanceAgent"
        elif "marketing" in input_data.lower():
            decision = "MarketingAgent"
        else:
            decision = "SummaryAgent"
            
        return {
            "result": {"agent": decision},
            "input": input_data,
            "confidence": 0.9
        }
    
    router = MagicMock()
    router.name = "RouterAgent"
    router.execute.side_effect = router_response
    return router

@pytest.fixture
def agents():
    """Fixture para crear agentes simulados."""
    return {
        "SummaryAgent": MockAgent("SummaryAgent", {"summary": "Resumen de prueba"}),
        "FinanceAgent": MockAgent("FinanceAgent", {"analysis": "Análisis financiero"}),
        "MarketingAgent": MockAgent("MarketingAgent", {"strategy": "Estrategia de marketing"})
    }

@pytest.fixture
def orchestrator(mock_router, agents):
    """Fixture para crear un orquestador con agentes simulados."""
    return Orchestrator(
        router_agent=mock_router,
        agents=agents,
        max_retries=2,
        confidence_threshold=0.7
    )

def test_router_agent(orchestrator):
    """Test que el RouterAgent selecciona el agente correcto."""
    # Solicitud para análisis
    analysis_input = {
        "query": "Analiza los patrones de comportamiento en este texto y extrae conclusiones",
        "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
    }
    
    # Solicitud para acción
    action_input = {
        "query": "Ejecuta el siguiente comando y proporciona los resultados",
        "action_request": "Crear un informe de ventas para el primer trimestre"
    }
    
    # Solicitud para resumen
    summary_input = {
        "query": "Resume el siguiente artículo manteniendo los puntos clave",
        "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    }
    
    # Ejecutar el agente router para cada solicitud
    router_result_analysis = orchestrator.router_agent._extract_agent_decision(
        '{"agent": "analysis", "confidence": 0.9, "reasoning": "La solicitud pide un análisis de patrones"}'
    )
    
    router_result_action = orchestrator.router_agent._extract_agent_decision(
        '{"agent": "action", "confidence": 0.85, "reasoning": "La solicitud pide ejecutar un comando"}'
    )
    
    router_result_summary = orchestrator.router_agent._extract_agent_decision(
        '{"agent": "summary", "confidence": 0.95, "reasoning": "La solicitud pide resumir un artículo"}'
    )
    
    # Verificar que se seleccionaron los agentes correctos
    assert router_result_analysis["agent"] == "analysis"
    assert router_result_action["agent"] == "action"
    assert router_result_summary["agent"] == "summary"
    
    # Verificar que las confianzas son razonables
    assert router_result_analysis["confidence"] > 0.5
    assert router_result_action["confidence"] > 0.5
    assert router_result_summary["confidence"] > 0.5

def test_route_selector(orchestrator):
    """Test que la función de selección de ruta funciona correctamente."""
    # Caso: Decisión válida con alta confianza
    state_valid = {
        "agent_decision": "analysis",
        "router_confidence": 0.9
    }
    assert orchestrator._route_selector(state_valid) == "analysis"
    
    # Caso: Decisión válida con baja confianza
    state_low_confidence = {
        "agent_decision": "action",
        "router_confidence": 0.3  # Por debajo del umbral
    }
    assert orchestrator._route_selector(state_low_confidence) == "analysis"  # Debería usar el valor por defecto
    
    # Caso: Decisión inválida
    state_invalid = {
        "agent_decision": "invalid_agent",
        "router_confidence": 0.8
    }
    assert orchestrator._route_selector(state_invalid) == "analysis"  # Debería usar el valor por defecto

@pytest.mark.asyncio
async def test_process_request_integration():
    """Test de integración del endpoint de procesamiento."""
    # Crear una solicitud de prueba
    test_request = {
        "query": "Resume el siguiente párrafo manteniendo los puntos clave",
        "content": "La inteligencia artificial (IA) es la simulación de procesos de inteligencia humana por parte de máquinas, especialmente sistemas informáticos. Estos procesos incluyen el aprendizaje, el razonamiento y la autocorrección. Las aplicaciones particulares de la IA incluyen sistemas expertos, procesamiento del lenguaje natural, reconocimiento de voz y visión artificial."
    }
    
    # Enviar la solicitud al endpoint
    response = client.post(
        "/api/v1/process",
        json=test_request
    )
    
    # Verificar la respuesta
    assert response.status_code == 200
    data = response.json()
    
    # Validar la estructura de la respuesta
    assert "status" in data
    assert "agent_used" in data
    assert "confidence" in data
    assert "result" in data
    
    # Verificar que se usó el agente de resumen
    assert data["agent_used"] == "summary"
    assert data["confidence"] > 0.5
    assert data["status"] == "success"

def test_orchestrator_initialization(orchestrator):
    """Test de inicialización del orquestador."""
    assert orchestrator.router_agent.name == "RouterAgent"
    assert len(orchestrator.agents) == 3
    assert orchestrator.max_retries == 2
    assert orchestrator.confidence_threshold == 0.7

def test_orchestrator_process_single_agent(orchestrator):
    """Test del procesamiento de una solicitud con un solo agente."""
    result = orchestrator.process("Necesito un resumen de este documento")
    
    assert result["status"] == "success"
    assert "agent_name" in result
    assert result["agent_name"] == "SummaryAgent"
    assert "result" in result
    assert "summary" in result["result"]
    assert result["confidence"] >= orchestrator.confidence_threshold

def test_orchestrator_process_specific_agent(orchestrator):
    """Test del procesamiento con un agente específico basado en la consulta."""
    result = orchestrator.process("Analiza estas finanzas corporativas")
    
    assert result["status"] == "success"
    assert result["agent_name"] == "FinanceAgent"
    assert "analysis" in result["result"]

def test_orchestrator_fallback_low_confidence(orchestrator, mock_router, agents):
    """Test del mecanismo de fallback cuando la confianza es baja."""
    # Configurar router para devolver baja confianza
    def low_confidence_response(input_data):
        return {
            "result": {"agent": "SummaryAgent"},
            "input": input_data,
            "confidence": 0.3  # Por debajo del umbral
        }
    
    mock_router.execute.side_effect = low_confidence_response
    
    # Configurar un agente de respaldo con alta confianza
    agents["SummaryAgent"].confidence = 0.9
    
    result = orchestrator.process("Consulta ambigua")
    
    assert result["status"] == "success"
    assert "fallback" in result
    assert result["fallback"] == True
    assert result["confidence"] >= orchestrator.confidence_threshold

def test_orchestrator_retry_mechanism(orchestrator, mock_router):
    """Test del mecanismo de reintento cuando falla la ejecución."""
    # Simular fallo en la primera llamada y éxito en la segunda
    fail_count = [0]
    
    def failing_router(input_data):
        if fail_count[0] == 0:
            fail_count[0] += 1
            raise Exception("Error simulado")
        else:
            return {
                "result": {"agent": "SummaryAgent"},
                "input": input_data,
                "confidence": 0.9
            }
    
    mock_router.execute.side_effect = failing_router
    
    result = orchestrator.process("Consulta con error")
    
    assert result["status"] == "success"
    assert result["retries"] == 1
    assert result["agent_name"] == "SummaryAgent"

def test_orchestrator_max_retries_exceeded(orchestrator, mock_router):
    """Test del manejo de errores cuando se excede el número máximo de reintentos."""
    # Configurar router para siempre fallar
    mock_router.execute.side_effect = Exception("Error persistente")
    
    result = orchestrator.process("Consulta problemática")
    
    assert result["status"] == "error"
    assert "error_message" in result
    assert "retries" in result
    assert result["retries"] == orchestrator.max_retries

def test_orchestrator_unknown_agent(orchestrator, mock_router):
    """Test del manejo de un agente desconocido."""
    # Configurar router para devolver un agente que no existe
    def unknown_agent_response(input_data):
        return {
            "result": {"agent": "UnknownAgent"},
            "input": input_data,
            "confidence": 0.9
        }
    
    mock_router.execute.side_effect = unknown_agent_response
    
    result = orchestrator.process("Consulta para agente desconocido")
    
    assert result["status"] == "error"
    assert "error_message" in result
    assert "UnknownAgent" in result["error_message"]

class TestOrchestrator:
    """Pruebas para el Orchestrator."""
    
    def setup_method(self):
        """Configuración inicial para cada prueba."""
        self.mock_router = MagicMock(spec=RouterAgent)
        self.mock_analysis = MagicMock(spec=AnalysisAgent)
        self.mock_action = MagicMock(spec=ActionAgent)
        self.mock_summary = MagicMock(spec=SummaryAgent)
        
        # Configurar orquestador con agentes mock
        self.orchestrator = Orchestrator(
            router_agent=self.mock_router,
            analysis_agent=self.mock_analysis,
            action_agent=self.mock_action,
            summary_agent=self.mock_summary,
            max_retries=2,
            confidence_threshold=0.7
        )
    
    def test_process_request_analysis(self):
        """Prueba el procesamiento de una solicitud que requiere análisis."""
        # Configurar respuesta del router
        self.mock_router.execute.return_value = {
            "status": "success",
            "agent_name": "RouterAgent",
            "result": {
                "agent_decision": "AnalysisAgent",
                "confidence": 0.9,
                "input": "Analiza este documento financiero"
            },
            "processing_time": 0.5
        }
        
        # Configurar respuesta del análisis
        self.mock_analysis.execute.return_value = {
            "status": "success",
            "agent_name": "AnalysisAgent",
            "result": {
                "analysis_result": "Este es un análisis detallado...",
                "confidence": 0.85,
                "input": "Analiza este documento financiero"
            },
            "processing_time": 1.2
        }
        
        # Ejecutar el orquestador
        result = self.orchestrator.process("Analiza este documento financiero")
        
        # Verificar que se llamó al router
        self.mock_router.execute.assert_called_once()
        
        # Verificar que se llamó al agente de análisis
        self.mock_analysis.execute.assert_called_once()
        
        # Verificar el resultado
        assert result["status"] == "success"
        assert "analysis_result" in result["result"]
        assert result["processing_time"] > 0

    def test_process_request_action(self):
        """Prueba el procesamiento de una solicitud que requiere acción."""
        # Configurar respuesta del router
        self.mock_router.execute.return_value = {
            "status": "success",
            "agent_name": "RouterAgent",
            "result": {
                "agent_decision": "ActionAgent",
                "confidence": 0.85,
                "input": "Genera un informe de ventas"
            },
            "processing_time": 0.4
        }
        
        # Configurar respuesta del agente de acción
        self.mock_action.execute.return_value = {
            "status": "success",
            "agent_name": "ActionAgent",
            "result": {
                "action_result": "Informe de ventas generado con éxito.",
                "confidence": 0.9,
                "input": "Genera un informe de ventas"
            },
            "processing_time": 2.1
        }
        
        # Ejecutar el orquestador
        result = self.orchestrator.process("Genera un informe de ventas")
        
        # Verificar que se llamó al router
        self.mock_router.execute.assert_called_once()
        
        # Verificar que se llamó al agente de acción
        self.mock_action.execute.assert_called_once()
        
        # Verificar el resultado
        assert result["status"] == "success"
        assert "action_result" in result["result"]

    def test_process_request_summary(self):
        """Prueba el procesamiento de una solicitud que requiere resumen."""
        # Configurar respuesta del router
        self.mock_router.execute.return_value = {
            "status": "success",
            "agent_name": "RouterAgent",
            "result": {
                "agent_decision": "SummaryAgent",
                "confidence": 0.95,
                "input": "Resume este documento extenso"
            },
            "processing_time": 0.3
        }
        
        # Configurar respuesta del agente de resumen
        self.mock_summary.execute.return_value = {
            "status": "success",
            "agent_name": "SummaryAgent",
            "result": {
                "summary_result": "Resumen del documento: puntos clave...",
                "confidence": 0.92,
                "input": "Resume este documento extenso"
            },
            "processing_time": 1.7
        }
        
        # Ejecutar el orquestador
        result = self.orchestrator.process("Resume este documento extenso")
        
        # Verificar que se llamó al router
        self.mock_router.execute.assert_called_once()
        
        # Verificar que se llamó al agente de resumen
        self.mock_summary.execute.assert_called_once()
        
        # Verificar el resultado
        assert result["status"] == "success"
        assert "summary_result" in result["result"]

    def test_low_confidence_retry(self):
        """Prueba el mecanismo de reintento cuando la confianza es baja."""
        # Primera respuesta del router con baja confianza
        self.mock_router.execute.return_value = {
            "status": "success",
            "agent_name": "RouterAgent",
            "result": {
                "agent_decision": "AnalysisAgent",
                "confidence": 0.5,  # Por debajo del umbral
                "input": "Consulta ambigua"
            },
            "processing_time": 0.4
        }
        
        # Segunda respuesta (después del reintento) con mayor confianza
        self.mock_router.execute.side_effect = [
            {
                "status": "success",
                "agent_name": "RouterAgent",
                "result": {
                    "agent_decision": "AnalysisAgent",
                    "confidence": 0.5,  # Primera ejecución - baja confianza
                    "input": "Consulta ambigua"
                },
                "processing_time": 0.4
            },
            {
                "status": "success",
                "agent_name": "RouterAgent",
                "result": {
                    "agent_decision": "ActionAgent",
                    "confidence": 0.8,  # Segunda ejecución - confianza adecuada
                    "input": "Consulta ambigua con contexto adicional"
                },
                "processing_time": 0.5
            }
        ]
        
        # Configurar respuesta del agente de acción
        self.mock_action.execute.return_value = {
            "status": "success",
            "agent_name": "ActionAgent",
            "result": {
                "action_result": "Acción completada con contexto adicional",
                "confidence": 0.85,
                "input": "Consulta ambigua con contexto adicional"
            },
            "processing_time": 1.3
        }
        
        # Ejecutar el orquestador
        result = self.orchestrator.process("Consulta ambigua")
        
        # Verificar que se llamó al router dos veces (original + reintento)
        assert self.mock_router.execute.call_count == 2
        
        # Verificar que se llamó al agente de acción después del reintento
        self.mock_action.execute.assert_called_once()
        
        # Verificar el resultado
        assert result["status"] == "success"
        assert "action_result" in result["result"]
        
    def test_error_handling(self):
        """Prueba el manejo de errores cuando un agente falla."""
        # Configurar respuesta del router
        self.mock_router.execute.return_value = {
            "status": "success",
            "agent_name": "RouterAgent",
            "result": {
                "agent_decision": "AnalysisAgent",
                "confidence": 0.9,
                "input": "Analiza este documento"
            },
            "processing_time": 0.3
        }
        
        # Configurar error en el agente de análisis
        self.mock_analysis.execute.return_value = {
            "status": "error",
            "agent_name": "AnalysisAgent",
            "error": "No se pudo procesar el documento",
            "processing_time": 0.8
        }
        
        # Ejecutar el orquestador
        result = self.orchestrator.process("Analiza este documento")
        
        # Verificar que se llamó al router
        self.mock_router.execute.assert_called_once()
        
        # Verificar que se llamó al agente de análisis
        self.mock_analysis.execute.assert_called_once()
        
        # Verificar el resultado de error
        assert result["status"] == "error"
        assert "error" in result 
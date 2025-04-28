import pytest
from fastapi.testclient import TestClient
import json
from app.main import app
from app.core.orchestrator import AgentOrchestrator

client = TestClient(app)

@pytest.fixture
def orchestrator():
    return AgentOrchestrator()

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
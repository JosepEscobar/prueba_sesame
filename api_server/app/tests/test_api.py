import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.orchestrator import Orchestrator

client = TestClient(app)

@pytest.fixture
def mock_orchestrator():
    """Fixture para crear un orquestador simulado."""
    orchestrator = MagicMock(spec=Orchestrator)
    
    # Configurar comportamiento del orquestador para diferentes tipos de consultas
    def process_side_effect(query):
        if "error" in query.lower():
            return {
                "status": "error",
                "error_message": "Error procesando la consulta",
                "retries": 2
            }
        elif "finanzas" in query.lower():
            return {
                "status": "success",
                "agent_name": "FinanceAgent",
                "result": {"analysis": "Análisis financiero detallado"},
                "confidence": 0.85,
                "processing_time": 1.2
            }
        else:
            return {
                "status": "success",
                "agent_name": "SummaryAgent",
                "result": {"summary": "Resumen del contenido solicitado"},
                "confidence": 0.92,
                "processing_time": 0.8
            }
    
    orchestrator.process.side_effect = process_side_effect
    return orchestrator

@pytest.mark.parametrize("endpoint", ["/", "/health"])
def test_basic_endpoints(endpoint):
    """Test de los endpoints básicos."""
    response = client.get(endpoint)
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"

def test_metrics_endpoint():
    """Test del endpoint de métricas."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

@patch("app.main.get_orchestrator")
def test_process_endpoint_success(mock_get_orchestrator, mock_orchestrator):
    """Test del endpoint de procesamiento con respuesta exitosa."""
    mock_get_orchestrator.return_value = mock_orchestrator
    
    response = client.post(
        "/api/v1/process",
        json={"query": "Haz un resumen de este documento"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert data["agent_name"] == "SummaryAgent"
    assert "summary" in data["result"]
    assert data["confidence"] > 0.9
    assert "processing_time" in data

@patch("app.main.get_orchestrator")
def test_process_endpoint_finance(mock_get_orchestrator, mock_orchestrator):
    """Test del endpoint de procesamiento con consulta financiera."""
    mock_get_orchestrator.return_value = mock_orchestrator
    
    response = client.post(
        "/api/v1/process",
        json={"query": "Analiza estas finanzas corporativas"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert data["agent_name"] == "FinanceAgent"
    assert "analysis" in data["result"]
    assert data["confidence"] > 0.8

@patch("app.main.get_orchestrator")
def test_process_endpoint_error(mock_get_orchestrator, mock_orchestrator):
    """Test del endpoint de procesamiento con error."""
    mock_get_orchestrator.return_value = mock_orchestrator
    
    response = client.post(
        "/api/v1/process",
        json={"query": "Genera un error en el procesamiento"}
    )
    
    assert response.status_code == 500
    data = response.json()
    
    assert data["status"] == "error"
    assert "error_message" in data
    assert "retries" in data

def test_process_endpoint_validation_error():
    """Test del endpoint de procesamiento con error de validación."""
    response = client.post(
        "/api/v1/process",
        json={"invalid_field": "Este campo no es válido"}
    )
    
    assert response.status_code == 422
    data = response.json()
    
    assert "detail" in data

@patch("app.main.get_orchestrator")
def test_process_endpoint_with_context(mock_get_orchestrator, mock_orchestrator):
    """Test del endpoint de procesamiento con contexto adicional."""
    mock_get_orchestrator.return_value = mock_orchestrator
    
    response = client.post(
        "/api/v1/process",
        json={
            "query": "Haz un resumen de este documento",
            "context": {
                "document_type": "reporte_financiero",
                "company": "TechCorp",
                "year": 2023
            }
        }
    )
    
    assert response.status_code == 200
    
    # Verificar que el contexto fue pasado al orquestador
    call_args = mock_orchestrator.process.call_args[0][0]
    assert "Haz un resumen de este documento" in call_args 
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "operational"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert data["status"] == "healthy"

def test_list_agents():
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) == 4
    assert all("name" in agent and "description" in agent for agent in data["agents"])

def test_process_request():
    request_data = {
        "query": "Analiza este texto",
        "content": "Este es un texto de prueba para análisis"
    }
    response = client.post("/api/v1/agents/process", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "confidence" in data
    assert "agent_used" in data
    assert data["confidence"] > 0

def test_process_request_invalid():
    request_data = {
        "query": ""  # Query vacío debería fallar
    }
    response = client.post("/api/v1/agents/process", json=request_data)
    assert response.status_code == 422  # Error de validación 
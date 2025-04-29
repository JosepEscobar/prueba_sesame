"""
Tests para el servidor MCP.
"""
import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import json

from app.tools.server.mcp_server import MCPToolServer, run_server
from app.core.metrics import MetricsCollector


@pytest.fixture
def mcp_server():
    """Fixture que proporciona una instancia de MCPToolServer para tests."""
    server = MCPToolServer(host="localhost", port=4321)
    return server


@pytest.fixture
def mock_schema_path(tmp_path):
    """Crea un archivo schema temporal para testing."""
    schema_dir = tmp_path / "schemas"
    schema_dir.mkdir()
    schema_path = schema_dir / "test_tool.json"
    
    schema = {
        "name": "test_tool",
        "description": "Una herramienta de prueba",
        "inputs": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Parámetro 1"}
            },
            "required": ["param1"]
        },
        "outputs": {
            "type": "object",
            "properties": {
                "result": {"type": "string", "description": "Resultado"}
            }
        }
    }
    
    with open(schema_path, 'w') as f:
        json.dump(schema, f)
        
    return schema_path


@pytest.mark.asyncio
async def test_register_tool_from_json(mcp_server, mock_schema_path):
    """Prueba el registro de una herramienta desde un archivo JSON."""
    result = mcp_server.register_tool_from_json(mock_schema_path)
    assert result == True
    assert hasattr(mcp_server, "_tool_schemas")
    assert "test_tool" in mcp_server._tool_schemas


@pytest.mark.asyncio
async def test_register_tool_implementation(mcp_server, mock_schema_path):
    """Prueba el registro de una implementación para una herramienta."""
    # Primero registramos el esquema
    mcp_server.register_tool_from_json(mock_schema_path)
    
    # Definimos una implementación simple
    def tool_implementation(params):
        return {"result": f"Procesado: {params.get('param1', '')}"}
    
    # Registramos la implementación
    result = mcp_server.register_tool_implementation("test_tool", tool_implementation)
    assert result == True


@pytest.mark.asyncio
async def test_start_server(mcp_server):
    """Prueba el inicio del servidor MCP."""
    with patch.object(mcp_server.mcp_server, 'create_server', new_callable=AsyncMock) as mock_start:
        # Configurar el mock para simular un comportamiento asíncrono
        mock_start.return_value = None
        
        # Llamar al método start_server
        result = await mcp_server.start_server()
        
        # Verificar que se llamó al método create_server con los argumentos correctos
        mock_start.assert_called_once_with(host=mcp_server.host, port=mcp_server.port)
        
        # Verificar que el resultado es True y el servidor está en ejecución
        assert result == True
        assert mcp_server.is_running() == True


@pytest.mark.asyncio
async def test_stop_server(mcp_server):
    """Prueba la detención del servidor MCP."""
    # Establecer que el servidor está en ejecución
    mcp_server._is_running = True
    
    # Llamar al método stop_server
    result = await mcp_server.stop_server()
    
    # Verificar que el resultado es True y el servidor no está en ejecución
    assert result == True
    assert mcp_server.is_running() == False


@pytest.mark.asyncio
async def test_run_server(mcp_server):
    """Prueba la función run_server."""
    with patch.object(mcp_server, 'start_server', new_callable=AsyncMock) as mock_start:
        with patch.object(mcp_server, 'is_running') as mock_running:
            # Configurar los mocks
            mock_start.return_value = True
            
            # Hacer que is_running() devuelva True una vez y luego False para terminar el bucle
            mock_running.side_effect = [True, False]
            
            # Ejecutar run_server con un tiempo de espera corto
            await run_server(mcp_server)
            
            # Verificar que se llamó a start_server
            mock_start.assert_called_once() 
"""
Tests para el servidor MCP principal (main.py)
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import main
from main import app


@pytest.fixture
def client():
    """Fixture para crear un cliente de prueba para el servidor FastAPI."""
    return TestClient(app)


class TestMCPServer:
    """Pruebas para el servidor MCP."""

    def test_root_endpoint(self, client):
        """Prueba que el endpoint raíz devuelve la información correcta."""
        # Hacer solicitud al endpoint raíz
        response = client.get("/")
        
        # Verificar respuesta
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "Servidor MCP de Sesame Tools" in data["message"]
        assert data["version"] == "1.0.0"

    def test_status_endpoint(self, client):
        """Prueba que el endpoint de estado devuelve la información correcta."""
        # Hacer solicitud al endpoint de estado
        response = client.get("/status")
        
        # Verificar respuesta
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "version" in data
        assert "tools_count" in data
        assert "tools" in data

    def test_list_tools_endpoint(self, client):
        """Prueba que el endpoint para listar herramientas funciona correctamente."""
        # Hacer solicitud al endpoint para listar herramientas
        response = client.get("/mcp/v1/tools")
        
        # Verificar respuesta
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        
        # Verificar que la lista de herramientas no está vacía
        assert len(data["tools"]) > 0
        
        # Verificar estructura de cada herramienta
        for tool in data["tools"]:
            assert "name" in tool
            assert "description" in tool

    def test_list_tools_root_endpoint(self, client):
        """Prueba que el endpoint alternativo para listar herramientas funciona correctamente."""
        # Hacer solicitud al endpoint alternativo
        response = client.get("/tools")
        
        # Verificar respuesta
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        
        # Verificar que la lista de herramientas no está vacía
        assert len(data["tools"]) > 0

    @pytest.mark.asyncio
    @patch('main.tools_registry')
    async def test_execute_tool_endpoint(self, mock_registry, client):
        """Prueba la ejecución de una herramienta a través del endpoint."""
        # Crear una herramienta mock que sea coroutine
        async def mock_tool_func(**params):
            return {"resultado": "Datos procesados correctamente"}
        
        # Configurar el registro mock
        mock_registry.__getitem__.return_value = mock_tool_func
        mock_registry.__contains__.return_value = True
        
        # Datos para la solicitud
        tool_name = "herramienta_test"
        params = {"param1": "valor1", "param2": 123}
        
        # Hacer solicitud para ejecutar la herramienta
        response = client.post(f"/mcp/v1/tools/{tool_name}", json=params)
        
        # Verificar respuesta
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert data["result"] == {"resultado": "Datos procesados correctamente"}

    @pytest.mark.asyncio
    @patch('main.tools_registry')
    async def test_execute_tool_not_found(self, mock_registry, client):
        """Prueba que se maneja correctamente una herramienta inexistente."""
        # Configurar el registro mock para que la herramienta no exista
        mock_registry.__contains__.return_value = False
        
        # Hacer solicitud para ejecutar una herramienta inexistente
        response = client.post("/mcp/v1/tools/herramienta_inexistente", json={})
        
        # Verificar respuesta de error
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "no encontrada" in data["detail"].lower()

    @pytest.mark.asyncio
    @patch('main.tools_registry')
    async def test_execute_tool_error(self, mock_registry, client):
        """Prueba que se manejan correctamente los errores durante la ejecución de una herramienta."""
        # Crear una herramienta mock que lanza una excepción
        async def mock_error_tool(**params):
            raise Exception("Error de prueba")
        
        # Configurar el registro mock
        mock_registry.__getitem__.return_value = mock_error_tool
        mock_registry.__contains__.return_value = True
        
        # Hacer solicitud para ejecutar la herramienta
        response = client.post("/mcp/v1/tools/herramienta_con_error", json={})
        
        # Verificar respuesta de error
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error en la ejecución" in data["detail"]
        assert "Error de prueba" in data["detail"]

    def test_tool_registration(self):
        """Prueba que el decorador de registro de herramientas funciona correctamente."""
        # Definir una función de prueba
        @main.register_tool(name="herramienta_prueba")
        async def funcion_prueba(param1, param2=None):
            """Descripción de la función de prueba."""
            return {"resultado": param1, "extra": param2}
        
        # Verificar que la función está registrada con el nombre correcto
        assert "herramienta_prueba" in main.tools_registry
        assert main.tools_registry["herramienta_prueba"] == funcion_prueba
        
        # Verificar que el decorador preserva la documentación
        assert funcion_prueba.__doc__ == "Descripción de la función de prueba."

    def test_tool_registration_sin_nombre(self):
        """Prueba que el decorador de registro de herramientas funciona sin nombre específico."""
        # Definir una función de prueba sin nombre específico
        @main.register_tool()
        async def otra_funcion_prueba(param1):
            """Otra función de prueba."""
            return {"resultado": param1}
        
        # Verificar que la función está registrada con su propio nombre
        assert "otra_funcion_prueba" in main.tools_registry
        assert main.tools_registry["otra_funcion_prueba"] == otra_funcion_prueba 
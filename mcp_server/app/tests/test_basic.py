"""
Tests básicos para verificar que el entorno de testing funciona correctamente.
"""

import os

import pytest


# Asegurar que estamos ejecutando desde el directorio correcto
def test_environment():
    """Verificar que el entorno de testing está configurado correctamente"""
    assert "TESTING" in os.environ
    assert os.environ["TESTING"] == "1"
    assert "ENVIRONMENT" in os.environ
    assert os.environ["ENVIRONMENT"] == "test"


# Verificar que podemos importar los módulos correctamente
def test_imports():
    """Verificar que podemos importar los módulos de la aplicación"""
    try:
        from app.core.config import get_settings

        settings = get_settings()
        assert settings is not None
    except ImportError as e:
        pytest.fail(f"Error al importar los módulos: {e}")


# Verificar el fixture
def test_mcp_server_fixture(mcp_server):
    """Verificar que el fixture del servidor MCP funciona"""
    assert mcp_server is not None
    assert "status" in mcp_server
    assert mcp_server["status"] == "active"

#!/usr/bin/env python3
"""
Configuración principal para pruebas con pytest.

Define fixtures y configuraciones comunes para toda la suite de pruebas.
"""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Añadir el directorio raíz al path para importar módulos correctamente
sys.path.insert(0, str(Path(__file__).parent))


# Fixtures comunes para tests
@pytest.fixture
def api_client() -> TestClient:
    """Fixture para crear un cliente de test para la API"""
    from fastapi.testclient import TestClient

    from main import app

    # Configurar el modo de prueba
    os.environ["APP_ENV"] = "test"

    return TestClient(app)

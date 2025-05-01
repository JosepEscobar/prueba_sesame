import os
import sys
from pathlib import Path

import pytest

# Agregar el directorio raíz al path para que los imports funcionen correctamente
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Configurar variables de entorno para testing
os.environ["ENVIRONMENT"] = "test"
os.environ["TESTING"] = "1"


# Fixtures comunes para tests
@pytest.fixture
def mcp_server():
    """Fixture para simular el servidor MCP para tests"""
    # Aquí se puede agregar lógica para crear un mock del servidor MCP
    return {"status": "active", "tools": []}

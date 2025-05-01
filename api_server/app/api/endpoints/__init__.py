"""
Endpoints API para la aplicación.

Este módulo exporta los endpoints disponibles para la API.
"""

from app.api.endpoints.health import health_controller
from app.api.endpoints.tools import router as tools_router

# Este archivo está vacío intencionalmente para que el directorio sea un paquete Python.
# Los endpoints se cargan dinámicamente en el router de la API.

# Exportamos explícitamente estos módulos
__all__ = ["health_controller", "tools_router"]

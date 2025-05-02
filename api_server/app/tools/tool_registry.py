"""
Registry para las herramientas MCP.

Este módulo mantiene un registro de las herramientas MCP disponibles
en el sistema y facilita la obtención de sus esquemas y funciones.
"""

from collections.abc import Callable
from typing import Any


class ToolRegistry:
    """
    Registro centralizado de herramientas MCP.

    Permite registrar herramientas, obtener sus esquemas y funciones,
    y enumerar las herramientas disponibles en el sistema.
    """

    def __init__(self):
        """
        Inicializa un nuevo registro de herramientas vacío.
        """
        self._schemas = {}  # Esquemas de las herramientas (nombre -> esquema)
        self._implementations = {}  # Implementaciones (nombre -> función)

    def register_schema(self, tool_name: str, schema: dict[str, Any]) -> None:
        """
        Registra el esquema de una herramienta.

        Args:
            tool_name: Nombre de la herramienta
            schema: Esquema JSON de la herramienta
        """
        self._schemas[tool_name] = schema

    def register_implementation(self, tool_name: str, implementation: Callable) -> None:
        """
        Registra la implementación de una herramienta.

        Args:
            tool_name: Nombre de la herramienta
            implementation: Función que implementa la herramienta
        """
        self._implementations[tool_name] = implementation

    def get_schema(self, tool_name: str) -> dict[str, Any] | None:
        """
        Obtiene el esquema de una herramienta por su nombre.

        Args:
            tool_name: Nombre de la herramienta

        Returns:
            Esquema de la herramienta o None si no existe
        """
        return self._schemas.get(tool_name)

    def get_implementation(self, tool_name: str) -> Callable | None:
        """
        Obtiene la implementación de una herramienta por su nombre.

        Args:
            tool_name: Nombre de la herramienta

        Returns:
            Implementación de la herramienta o None si no existe
        """
        return self._implementations.get(tool_name)

    def list_tools(self) -> list[str]:
        """
        Lista los nombres de todas las herramientas registradas.

        Returns:
            Lista de nombres de herramientas
        """
        return list(set(self._schemas.keys()) | set(self._implementations.keys()))

    def list_implemented_tools(self) -> list[str]:
        """
        Lista los nombres de las herramientas que tienen implementación.

        Returns:
            Lista de nombres de herramientas con implementación
        """
        return list(self._implementations.keys())

    def get_tool_details(self) -> list[dict[str, Any]]:
        """
        Obtiene detalles de todas las herramientas registradas.

        Returns:
            Lista de detalles de herramientas (nombre, descripción,
            tiene implementación)
        """
        details = []
        for tool_name in self.list_tools():
            schema = self.get_schema(tool_name)
            has_implementation = tool_name in self._implementations

            detail = {
                "name": tool_name,
                "description": schema.get("description", "") if schema else "",
                "has_implementation": has_implementation,
            }
            details.append(detail)

        return details


# Instancia global del registro de herramientas
tool_registry = ToolRegistry()

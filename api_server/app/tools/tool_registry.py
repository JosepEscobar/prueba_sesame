import glob
import json
import os
from typing import Any

from app.core.logging import logger


class ToolRegistry:
    """
    Registro centralizado de herramientas disponibles para los agentes.
    
    Proporciona una interfaz única para registrar, descubrir y acceder
    a las diferentes herramientas que pueden utilizar los agentes del sistema.
    """

    def __init__(self):
        """Inicializa el registro de herramientas."""
        # Mapeo de nombre de herramienta -> definición de herramienta
        self.tools: dict[str, dict[str, Any]] = {}
        # Mapeo de nombre de herramienta -> implementación
        self.implementations: dict[str, Any] = {}
        # Directorio donde se encuentran los esquemas
        self.schema_dir = os.path.join(os.path.dirname(__file__), "schemas")

        # Cargar esquemas de herramientas automáticamente
        self._load_tool_schemas()

    def _load_tool_schemas(self) -> None:
        """Carga los esquemas de herramientas desde el directorio de esquemas."""
        schema_files = glob.glob(os.path.join(self.schema_dir, "*.json"))

        for schema_file in schema_files:
            try:
                with open(schema_file, encoding='utf-8') as f:
                    schema = json.load(f)

                tool_name = schema.get("name")
                if not tool_name:
                    logger.warning(f"Esquema sin nombre en archivo {schema_file}, omitiendo")
                    continue

                self.tools[tool_name] = schema
                logger.info(f"Herramienta '{tool_name}' cargada desde {os.path.basename(schema_file)}")

            except Exception as e:
                logger.error(f"Error al cargar esquema desde {schema_file}: {str(e)}")

    def register_tool_implementation(self, tool_name: str, implementation: Any) -> bool:
        """
        Registra la implementación de una herramienta.
        
        Args:
            tool_name: Nombre de la herramienta (debe coincidir con el esquema)
            implementation: Implementación de la herramienta (función, clase, etc.)
            
        Returns:
            True si se registró correctamente, False en caso contrario
        """
        if tool_name not in self.tools:
            logger.warning(f"Intento de registrar implementación para herramienta '{tool_name}' sin esquema definido")
            return False

        self.implementations[tool_name] = implementation
        logger.info(f"Implementación para herramienta '{tool_name}' registrada")
        return True

    def get_tool_schema(self, tool_name: str) -> dict[str, Any] | None:
        """
        Obtiene el esquema de una herramienta por su nombre.
        
        Args:
            tool_name: Nombre de la herramienta
            
        Returns:
            Esquema de la herramienta o None si no existe
        """
        return self.tools.get(tool_name)

    def get_tool_implementation(self, tool_name: str) -> Any | None:
        """
        Obtiene la implementación de una herramienta por su nombre.
        
        Args:
            tool_name: Nombre de la herramienta
            
        Returns:
            Implementación de la herramienta o None si no existe
        """
        return self.implementations.get(tool_name)

    def list_tools(self) -> list[str]:
        """
        Lista los nombres de todas las herramientas registradas.
        
        Returns:
            Lista de nombres de herramientas
        """
        return list(self.tools.keys())

    def list_tools_with_implementations(self) -> list[str]:
        """
        Lista los nombres de las herramientas que tienen implementación.
        
        Returns:
            Lista de nombres de herramientas con implementación
        """
        return list(self.implementations.keys())

    def get_tool_details(self) -> list[dict[str, Any]]:
        """
        Obtiene detalles de todas las herramientas registradas.
        
        Returns:
            Lista de detalles de herramientas (nombre, descripción, tiene implementación)
        """
        details = []
        for name, schema in self.tools.items():
            details.append({
                "name": name,
                "description": schema.get("description", ""),
                "has_implementation": name in self.implementations
            })
        return details

# Instancia global del registro de herramientas
tool_registry = ToolRegistry()

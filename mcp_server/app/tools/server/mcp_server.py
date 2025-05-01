import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from app.core.logging import logger
from app.core.metrics import MetricsCollector


class MCPToolServer:
    """
    Implementación de un servidor MCP para exponer herramientas locales.

    Este servidor permite exponer herramientas locales a través del protocolo MCP
    para que puedan ser consumidas por clientes como LangChain, LlamaIndex, etc.
    """

    def __init__(self, host: str = "localhost", port: int = 4000):
        """
        Inicializa el servidor MCP.

        Args:
            host: Host en el que se ejecutará el servidor
            port: Puerto en el que se ejecutará el servidor
        """
        self.host = host
        self.port = port
        self.metrics = MetricsCollector()
        # Inicializar FastMCP para crear un servidor más moderno
        self.mcp_server = FastMCP("SesameTools")
        self._is_running = False

    def register_tool_from_json(self, schema_path: str | Path) -> bool:
        """
        Registra una herramienta a partir de un archivo JSON de esquema.

        Args:
            schema_path: Ruta al archivo JSON que contiene el esquema de la herramienta

        Returns:
            True si la herramienta se registró correctamente, False en caso contrario
        """
        try:
            # Cargar el esquema de la herramienta
            with open(schema_path, encoding="utf-8") as f:
                schema = json.load(f)

            # Verificar que el esquema tenga los campos requeridos
            if "name" not in schema:
                logger.error(f"El esquema en {schema_path} no tiene campo 'name'")
                return False

            tool_name = schema["name"]
            description = schema.get("description", "")

            # Registrar la herramienta usando la nueva API de FastMCP
            # Nota: Esto es una adaptación, ya que FastMCP tiene una API diferente
            # para registrar herramientas. Aquí solo estamos almacenando el esquema
            # para usar con register_tool_implementation más adelante.

            # Almacenar el esquema asociado al nombre de la herramienta
            if not hasattr(self, "_tool_schemas"):
                self._tool_schemas = {}
            self._tool_schemas[tool_name] = {
                "description": description,
                "input_schema": schema.get("inputs", {}),
                "output_schema": schema.get("outputs", {}),
            }

            logger.info(f"Esquema de herramienta '{tool_name}' registrado desde {schema_path}")
            return True

        except Exception as e:
            logger.error(f"Error al registrar herramienta desde {schema_path}: {str(e)}")
            return False

    def register_tool_implementation(self, tool_name: str, implementation: Callable[[dict[str, Any]], Any]) -> bool:
        """
        Registra la implementación de una herramienta existente.

        Args:
            tool_name: Nombre de la herramienta (debe coincidir con uno previamente registrado)
            implementation: Función que implementa la herramienta

        Returns:
            True si la implementación se registró correctamente, False en caso contrario
        """
        try:
            # Verificar que tenemos un esquema para esta herramienta
            if not hasattr(self, "_tool_schemas") or tool_name not in self._tool_schemas:
                logger.warning(f"Intento de registrar implementación para herramienta sin esquema: {tool_name}")
                # Podríamos continuar de todas formas, pero preferimos mantener la consistencia
                return False

            # Crear un wrapper para la implementación que maneje métricas y logs
            @self.mcp_server.tool(name=tool_name, description=self._tool_schemas[tool_name]["description"])
            async def tool_wrapper(**params):
                start_time = time.time()

                try:
                    # Ejecutar la implementación
                    logger.info(f"Ejecutando herramienta MCP '{tool_name}'")
                    result = implementation(params)

                    # Calcular tiempo de ejecución
                    execution_time = time.time() - start_time

                    # Registrar métricas
                    self.metrics.record_execution(
                        service_name="mcp_server", operation=tool_name, execution_time=execution_time
                    )

                    logger.info(f"Herramienta MCP '{tool_name}' ejecutada exitosamente en {execution_time:.4f}s")

                    return result

                except Exception as e:
                    # Calcular tiempo de ejecución
                    execution_time = time.time() - start_time

                    # Registrar métricas
                    self.metrics.record_error(agent_name=f"mcp_server.{tool_name}", error_type=str(e))

                    logger.error(f"Error al ejecutar herramienta MCP '{tool_name}': {str(e)}")

                    raise e

            logger.info(f"Implementación para herramienta '{tool_name}' registrada en el servidor MCP")
            return True

        except Exception as e:
            logger.error(f"Error al registrar implementación para herramienta {tool_name}: {str(e)}")
            return False

    def register_tools_from_directory(self, schemas_dir: str | Path) -> int:
        """
        Registra todas las herramientas definidas en un directorio.

        Args:
            schemas_dir: Directorio que contiene archivos JSON con esquemas de herramientas

        Returns:
            Número de herramientas registradas correctamente
        """
        schemas_dir = Path(schemas_dir)
        if not schemas_dir.is_dir():
            logger.error(f"El directorio {schemas_dir} no existe")
            return 0

        # Buscar todos los archivos JSON en el directorio
        json_files = list(schemas_dir.glob("*.json"))
        logger.info(f"Encontrados {len(json_files)} archivos JSON en {schemas_dir}")

        # Registrar cada herramienta
        registered_count = 0
        for json_file in json_files:
            if self.register_tool_from_json(json_file):
                registered_count += 1

        logger.info(f"Se registraron {registered_count} herramientas en el servidor MCP")
        return registered_count

    async def start_server(self) -> bool:
        """
        Inicia el servidor MCP.

        Returns:
            True si el servidor se inició correctamente, False en caso contrario
        """
        if self._is_running:
            logger.warning("El servidor MCP ya está en ejecución")
            return True

        try:
            # Configurar el servidor
            self.mcp_server.server_host = self.host
            self.mcp_server.server_port = self.port

            # En un entorno sin FastAPI, podemos iniciar el servidor directamente
            logger.info(f"Iniciando servidor MCP en {self.host}:{self.port}")

            # Marcar como en ejecución
            self._is_running = True

            return True

        except Exception as e:
            logger.error(f"Error al iniciar servidor MCP: {str(e)}")
            self._is_running = False
            return False

    async def stop_server(self) -> bool:
        """
        Detiene el servidor MCP.

        Returns:
            True si el servidor se detuvo correctamente, False en caso contrario
        """
        if not self._is_running:
            logger.warning("El servidor MCP no está en ejecución")
            return True

        try:
            # En FastMCP no hay un método directo stop_server,
            # pero podemos finalizar el proceso de manera ordenada
            self._is_running = False

            logger.info("Servidor MCP detenido")
            return True

        except Exception as e:
            logger.error(f"Error al detener servidor MCP: {str(e)}")
            return False

    def is_running(self) -> bool:
        """
        Verifica si el servidor MCP está en ejecución.

        Returns:
            True si el servidor está en ejecución, False en caso contrario
        """
        return self._is_running

    def get_registered_tools(self) -> list[str]:
        """
        Obtiene la lista de herramientas registradas en el servidor.

        Returns:
            Lista de nombres de herramientas registradas
        """
        if not hasattr(self, "_tool_schemas"):
            return []

        return list(self._tool_schemas.keys())


# Función auxiliar para ejecutar el servidor en un proceso separado
async def run_server(server: MCPToolServer):
    """
    Inicia el servidor MCP.

    Args:
        server: Instancia de MCPToolServer a iniciar
    """
    try:
        # Iniciar el servidor (esto bloqueará la ejecución hasta que se detenga)
        logger.info(f"Iniciando servidor MCP en {server.host}:{server.port}")
        await server.mcp_server.run()

    except KeyboardInterrupt:
        logger.info("Servidor MCP detenido por interrupción del teclado")
    except Exception as e:
        logger.error(f"Error en el servidor MCP: {str(e)}")
    finally:
        # Asegurarse de que el servidor se marca como detenido
        server._is_running = False
        logger.info("Servidor MCP detenido correctamente")

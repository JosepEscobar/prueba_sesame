from typing import Dict, Any, List, Optional, Callable, Union
import asyncio
import time
from pathlib import Path
import json
import os

import mcp
from mcp.server import MCPToolRegistry, MCPServer
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
        self.tool_registry = MCPToolRegistry()
        self.server = None
        self._is_running = False
    
    def register_tool_from_json(self, schema_path: Union[str, Path]) -> bool:
        """
        Registra una herramienta a partir de un archivo JSON de esquema.
        
        Args:
            schema_path: Ruta al archivo JSON que contiene el esquema de la herramienta
            
        Returns:
            True si la herramienta se registró correctamente, False en caso contrario
        """
        try:
            # Cargar el esquema de la herramienta
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # Verificar que el esquema tenga los campos requeridos
            if "name" not in schema:
                logger.error(f"El esquema en {schema_path} no tiene campo 'name'")
                return False
            
            tool_name = schema["name"]
            description = schema.get("description", "")
            
            # Registrar la herramienta sin implementación (solo esquema)
            self.tool_registry.add_tool(
                name=tool_name,
                description=description,
                input_schema=schema.get("inputs", {}),
                output_schema=schema.get("outputs", {})
            )
            
            logger.info(f"Herramienta '{tool_name}' registrada en el servidor MCP desde {schema_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error al registrar herramienta desde {schema_path}: {str(e)}")
            return False
    
    def register_tool_implementation(self, 
                                     tool_name: str, 
                                     implementation: Callable[[Dict[str, Any]], Dict[str, Any]]) -> bool:
        """
        Registra la implementación de una herramienta existente.
        
        Args:
            tool_name: Nombre de la herramienta (debe coincidir con uno previamente registrado)
            implementation: Función que implementa la herramienta
            
        Returns:
            True si la implementación se registró correctamente, False en caso contrario
        """
        try:
            # Verificar que la herramienta existe en el registro
            if tool_name not in [tool.name for tool in self.tool_registry.list_tools()]:
                logger.warning(f"Intento de registrar implementación para herramienta no definida: {tool_name}")
                return False
            
            # Crear un wrapper para la implementación que maneje métricas y logs
            async def implementation_wrapper(params: Dict[str, Any]) -> Dict[str, Any]:
                start_time = time.time()
                
                try:
                    # Ejecutar la implementación
                    logger.info(f"Ejecutando herramienta MCP '{tool_name}'")
                    result = implementation(params)
                    
                    # Calcular tiempo de ejecución
                    execution_time = time.time() - start_time
                    
                    # Registrar métricas
                    self.metrics.record_tool_execution(
                        tool_name=f"mcp_server.{tool_name}",
                        success=True,
                        execution_time=execution_time
                    )
                    
                    logger.info(f"Herramienta MCP '{tool_name}' ejecutada exitosamente en {execution_time:.4f}s")
                    
                    # Si la implementación devuelve un diccionario, devolverlo directamente
                    if isinstance(result, dict):
                        return result
                    
                    # Si la implementación devuelve otro tipo, envolverlo en un diccionario
                    return {"result": result}
                    
                except Exception as e:
                    # Calcular tiempo de ejecución
                    execution_time = time.time() - start_time
                    
                    # Registrar métricas
                    self.metrics.record_tool_execution(
                        tool_name=f"mcp_server.{tool_name}",
                        success=False,
                        execution_time=execution_time,
                        error=str(e)
                    )
                    
                    logger.error(f"Error al ejecutar herramienta MCP '{tool_name}': {str(e)}")
                    
                    return {"error": str(e)}
            
            # Registrar la implementación
            self.tool_registry.set_tool_implementation(tool_name, implementation_wrapper)
            logger.info(f"Implementación para herramienta '{tool_name}' registrada en el servidor MCP")
            
            return True
            
        except Exception as e:
            logger.error(f"Error al registrar implementación para herramienta {tool_name}: {str(e)}")
            return False
    
    def register_tools_from_directory(self, schemas_dir: Union[str, Path]) -> int:
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
            # Crear el servidor MCP
            self.server = MCPServer(
                host=self.host,
                port=self.port,
                tool_registry=self.tool_registry
            )
            
            # Iniciar el servidor
            await self.server.start()
            self._is_running = True
            
            logger.info(f"Servidor MCP iniciado en http://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Error al iniciar servidor MCP: {str(e)}")
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
            # Detener el servidor
            await self.server.stop()
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


# Función auxiliar para ejecutar el servidor en un proceso separado
async def run_server(server: MCPToolServer):
    """
    Ejecuta el servidor MCP y lo mantiene en ejecución.
    
    Args:
        server: Instancia de MCPToolServer a ejecutar
    """
    await server.start_server()
    
    try:
        # Mantener el servidor en ejecución
        while server.is_running():
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Deteniendo servidor MCP...")
        await server.stop_server()
    
    logger.info("Servidor MCP finalizado") 
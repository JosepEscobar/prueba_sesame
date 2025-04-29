from typing import Dict, Any, List, Optional, Awaitable, Callable
import asyncio
from functools import partial

from langchain_mcp.adapters import MCPClient as LangChainMCPClient
from app.core.logging import logger
from app.core.metrics import MetricsCollector

class MCPClientOfficial:
    """
    Cliente para interactuar con servidores MCP (Model Context Protocol) utilizando
    la implementación oficial proporcionada por la biblioteca langchain-mcp-adapters.
    
    Permite a los agentes acceder a herramientas externas de forma estandarizada y compatible
    con la especificación oficial del MCP.
    """
    
    def __init__(self, base_url: str = "http://localhost:4000"):
        """
        Inicializa el cliente MCP oficial.
        
        Args:
            base_url: URL base del servidor MCP
        """
        self.base_url = base_url
        self.metrics = MetricsCollector()
        self._client = LangChainMCPClient(base_url=base_url)
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
    
    async def initialize(self):
        """
        Inicializa la conexión y carga las herramientas disponibles.
        
        Esta función debe ser llamada antes de usar cualquier operación del cliente.
        """
        try:
            # Intentar obtener las herramientas disponibles para verificar la conexión
            await self.list_tools()
            logger.info(f"Cliente MCP inicializado correctamente en {self.base_url}")
            return True
        except Exception as e:
            logger.error(f"Error al inicializar cliente MCP en {self.base_url}: {str(e)}")
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        Lista las herramientas disponibles en el servidor MCP.
        
        Returns:
            Lista de herramientas disponibles con sus esquemas
        """
        if self._tools_cache:
            return self._tools_cache
        
        try:
            # Obtener herramientas del servidor MCP
            tools = await self._client.list_tools()
            
            # Convertir herramientas a formato esperado
            self._tools_cache = [
                {
                    "name": tool.tool_name,
                    "description": tool.tool_config.description,
                    "inputs": tool.tool_config.input_schema,
                    "outputs": tool.tool_config.output_schema
                }
                for tool in tools
            ]
            
            logger.info(f"Herramientas MCP cargadas: {len(self._tools_cache)}")
            return self._tools_cache
            
        except Exception as e:
            logger.error(f"Error al listar herramientas MCP: {str(e)}")
            return []
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Llama a una herramienta específica en el servidor MCP.
        
        Args:
            tool_name: Nombre de la herramienta a llamar
            params: Parámetros para la herramienta
            
        Returns:
            Resultado de la llamada a la herramienta
        """
        try:
            start_time = asyncio.get_event_loop().time()
            logger.info(f"Llamando a herramienta MCP: {tool_name}")
            
            # Ejecutar la herramienta
            result = await self._client.call_tool(tool_name, params)
            
            # Calcular tiempo de ejecución
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Registrar métricas
            self.metrics.record_tool_execution(
                tool_name=f"mcp.{tool_name}",
                success=True,
                execution_time=execution_time
            )
            
            logger.info(f"Herramienta MCP '{tool_name}' ejecutada exitosamente en {execution_time:.4f}s")
            
            return result.tool_result
                
        except Exception as e:
            # Registrar el error
            logger.error(f"Error al llamar a herramienta MCP {tool_name}: {str(e)}")
            self.metrics.record_tool_execution(
                tool_name=f"mcp.{tool_name}",
                success=False,
                execution_time=0.0,
                error=str(e)
            )
            
            return {"error": f"Error en la llamada a la herramienta: {str(e)}"}
    
    async def get_tool_wrapper(self, tool_name: str) -> Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]]:
        """
        Obtiene una función wrapper para una herramienta específica.
        
        Args:
            tool_name: Nombre de la herramienta
            
        Returns:
            Función wrapper que puede ser llamada con los parámetros de la herramienta
        """
        # Verificar que la herramienta existe
        tools = await self.list_tools()
        tool_exists = any(tool["name"] == tool_name for tool in tools)
        
        if not tool_exists:
            logger.warning(f"Intento de obtener wrapper para herramienta inexistente: {tool_name}")
            return None
        
        # Crear un wrapper para la herramienta
        async def tool_wrapper(params: Dict[str, Any]) -> Dict[str, Any]:
            return await self.call_tool(tool_name, params)
        
        return tool_wrapper
    
    async def close(self):
        """Cierra la conexión con el servidor MCP."""
        try:
            # El cliente oficial debería encargarse de cerrar las conexiones
            # pero podemos agregar limpieza adicional aquí si es necesario
            self._tools_cache = None
            logger.info("Cliente MCP cerrado")
        except Exception as e:
            logger.error(f"Error al cerrar cliente MCP: {str(e)}") 
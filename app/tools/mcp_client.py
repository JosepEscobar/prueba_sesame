from typing import Dict, Any, List, Optional, Awaitable, Callable
import asyncio
from functools import partial

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from app.core.logging import logger
from app.core.metrics import MetricsCollector

class MCPClient:
    """
    Cliente para interactuar con servidores MCP (Model Context Protocol) utilizando
    la implementación proporcionada por la biblioteca langchain-mcp-adapters.
    
    Permite a los agentes acceder a herramientas externas de forma estandarizada y compatible
    con la especificación del MCP.
    """
    
    def __init__(self, base_url: str = "http://localhost:4000"):
        """
        Inicializa el cliente MCP.
        
        Args:
            base_url: URL base del servidor MCP
        """
        self.base_url = base_url
        self.metrics = MetricsCollector()
        self._client = None
        self._tools_cache = None
    
    async def initialize(self):
        """
        Inicializa la conexión y carga las herramientas disponibles.
        
        Esta función debe ser llamada antes de usar cualquier operación del cliente.
        """
        try:
            # Crear el cliente MultiServerMCP
            self._client = MultiServerMCPClient({
                "default": {
                    "transport": "sse",
                    "url": self.base_url,
                }
            })
            
            # Cargar las herramientas disponibles
            await self.list_tools_async()
            logger.info(f"Cliente MCP inicializado correctamente en {self.base_url}")
            return True
        except Exception as e:
            logger.error(f"Error al inicializar cliente MCP en {self.base_url}: {str(e)}")
            return False
    
    async def list_tools_async(self) -> List[Dict[str, Any]]:
        """
        Lista las herramientas disponibles en el servidor MCP (versión asíncrona).
        
        Returns:
            Lista de herramientas disponibles con sus esquemas
        """
        if self._tools_cache is not None:
            return self._tools_cache
        
        try:
            if self._client is None:
                await self.initialize()
                
            # Detectar posibles problemas
            if not hasattr(self._client, 'get_tools'):
                logger.error("El cliente MCP no tiene el método get_tools")
                return []
                
            try:
                # Obtener herramientas del servidor MCP de manera segura
                # A veces get_tools devuelve una lista directamente en lugar de una coroutine
                get_tools_result = self._client.get_tools()
                
                # Comprobar si el resultado es una coroutine que podemos esperar
                if hasattr(get_tools_result, '__await__'):
                    # Es una coroutine, podemos usar await
                    tools = await get_tools_result
                else:
                    # No es una coroutine, usamos directamente el resultado
                    tools = get_tools_result
                    
                # Si es None o vacío, devolver lista vacía
                if not tools:
                    logger.warning("No se encontraron herramientas en el servidor MCP")
                    return []
                
                # Convertir herramientas a formato esperado
                self._tools_cache = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputs": {k: v for k, v in tool.args.items()},
                        "outputs": {"result": {"type": "any", "description": "Resultado de la operación"}}
                    }
                    for tool in tools
                ]
                
                logger.info(f"Herramientas MCP cargadas: {len(self._tools_cache)}")
                return self._tools_cache
                
            except (AttributeError, TypeError) as e:
                logger.error(f"Error al acceder a las propiedades de las herramientas: {str(e)}")
                return []
                
        except Exception as e:
            logger.error(f"Error al listar herramientas MCP: {str(e)}")
            return []
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Lista las herramientas disponibles en el servidor MCP (versión no asíncrona).
        Usa el caché si está disponible para evitar llamadas asíncronas.
        
        Returns:
            Lista de herramientas disponibles con sus esquemas
        """
        if self._tools_cache is not None:
            return self._tools_cache
        
        try:
            # Si no hay caché, intenta obtener herramientas de forma segura
            # sin romper el bucle existente
            try:
                # Si el bucle ya está en ejecución, no podemos usar run_until_complete
                asyncio.get_running_loop()
                # Devolver una lista vacía por ahora, y una tarea en segundo plano
                # actualizará el caché para futuras llamadas
                if not hasattr(self, "_update_cache_task") or self._update_cache_task.done():
                    # Crear tarea para actualizar caché en segundo plano
                    self._update_cache_task = asyncio.create_task(self._update_tools_cache())
                logger.warning("Operación asíncrona ejecutada durante bucle de eventos activo: se devuelve lista vacía")
                return []
            except RuntimeError:
                # No hay bucle en ejecución, podemos usar run_until_complete
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    self._tools_cache = loop.run_until_complete(self.list_tools_async())
                finally:
                    loop.close()
                return self._tools_cache
                
        except Exception as e:
            logger.error(f"Error al listar herramientas MCP (modo síncrono): {str(e)}")
            return []
            
    async def _update_tools_cache(self):
        """Actualiza el caché de herramientas en segundo plano."""
        try:
            self._tools_cache = await self.list_tools_async()
            logger.info(f"Caché de herramientas MCP actualizado en segundo plano: {len(self._tools_cache)}")
        except Exception as e:
            logger.error(f"Error al actualizar caché de herramientas MCP: {str(e)}")
    
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
            
            # Verificar si el cliente está inicializado
            if self._client is None:
                await self.initialize()
                
            # Obtener la herramienta
            tools = await self._client.get_tools()
            tool = next((t for t in tools if t.name == tool_name), None)
            
            if tool is None:
                raise ValueError(f"Herramienta '{tool_name}' no encontrada")
            
            # Ejecutar la herramienta
            result = await tool.ainvoke(params)
            
            # Calcular tiempo de ejecución
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Registrar métricas
            self.metrics.record_execution(
                service_name="mcp_client",
                operation=tool_name,
                execution_time=execution_time
            )
            
            logger.info(f"Herramienta MCP '{tool_name}' ejecutada exitosamente en {execution_time:.4f}s")
            
            # Procesar el resultado
            # En el nuevo adaptador, el resultado puede tener varios formatos
            # Intentamos estandarizar la salida
            
            # Si el resultado es una tupla (contenido, artefactos), tomamos solo el contenido
            if isinstance(result, tuple) and len(result) == 2:
                content = result[0]
                # Si content es un string, lo devolvemos directamente
                if isinstance(content, str):
                    return {"result": content}
                # Si es una lista de mensajes complejos, intentamos extraer el texto
                return {"result": content}
            
            # Para otros tipos de resultados, los devolvemos como están
            return {"result": result}
                
        except Exception as e:
            # Registrar el error
            logger.error(f"Error al llamar a herramienta MCP {tool_name}: {str(e)}")
            self.metrics.record_error(
                agent_name=f"mcp_client.{tool_name}", 
                error_type=str(e)
            )
            
            return {"error": f"Error en la llamada a la herramienta: {str(e)}"}
    
    async def invoke_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Alias para call_tool para mantener consistencia de nombres.
        """
        return await self.call_tool(tool_name, params)
    
    async def get_tool_wrapper(self, tool_name: str) -> Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]]:
        """
        Obtiene una función wrapper para una herramienta específica.
        
        Args:
            tool_name: Nombre de la herramienta
            
        Returns:
            Función wrapper que puede ser llamada con los parámetros de la herramienta
        """
        # Verificar que la herramienta existe
        tools = await self.list_tools_async()
        tool_exists = any(tool["name"] == tool_name for tool in tools)
        
        if not tool_exists:
            logger.warning(f"Intento de obtener wrapper para herramienta inexistente: {tool_name}")
            return None
        
        # Crear un wrapper para la herramienta
        async def tool_wrapper(params: Dict[str, Any]) -> Dict[str, Any]:
            return await self.call_tool(tool_name, params)
        
        return tool_wrapper
    
    # Métodos síncronos para compatibilidad
    def initialize_sync(self) -> bool:
        """Versión síncrona de initialize()."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.initialize())
    
    def list_tools_sync(self) -> List[Dict[str, Any]]:
        """Versión síncrona de list_tools_async()."""
        return self.list_tools()
    
    def call_tool_sync(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Versión síncrona de call_tool()."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.call_tool(tool_name, params))
    
    async def close(self):
        """Cierra la conexión con el servidor MCP."""
        try:
            if self._client is not None:
                await self._client.close()
                
            self._tools_cache = None
            self._client = None
            logger.info("Cliente MCP cerrado")
        except Exception as e:
            logger.error(f"Error al cerrar cliente MCP: {str(e)}") 
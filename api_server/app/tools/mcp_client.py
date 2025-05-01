"""
Cliente MCP con métodos sincronos para integración con agentes y LangGraph.

Este módulo proporciona una clase de cliente MCP que ofrece métodos sincronos
para poder ser usado fácilmente con agentes en entornos que no son asíncronos.
"""

import asyncio
import os
import subprocess
from collections.abc import Awaitable, Callable
from typing import Any

import requests
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.core.logging import logger
from app.core.metrics import MetricsCollector
from app.tools.stdio_client import StdioClientSession


class MCPClient:
    """
    Cliente MCP con métodos sincronos para interactuar con el servidor MCP.
    
    Esta implementación soporta tanto comunicación HTTP como stdio con el servidor MCP.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:4000",
        use_stdio: bool = False,
        mcp_server_path: str | None = None
    ):
        """
        Inicializa el cliente MCP.
        
        Args:
            base_url: URL base del servidor MCP para llamadas HTTP
            use_stdio: Si es True, utiliza comunicación por stdio con subprocess
            mcp_server_path: Ruta al servidor MCP para uso con stdio
        """
        self.base_url = base_url
        self.use_stdio = use_stdio
        self.mcp_server_path = mcp_server_path
        self.mcp_process = None
        self.tools_cache = None
        self.initialized = False
        self.metrics = MetricsCollector()

    def initialize_sync(self) -> bool:
        """
        Implementación puramente síncrona del método de inicialización.
        No intenta usar el loop de eventos en absoluto.
        
        Returns:
            bool: True si se inicializó con éxito, False en caso contrario
        """
        try:
            # Verificar que el servidor MCP está disponible mediante una llamada HTTP síncrona
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code != 200:
                logger.error(f"Error al verificar estado del servidor MCP: {response.status_code}")
                return False

            logger.info(f"Conexión con servidor MCP establecida en {self.base_url}")
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Error en inicialización síncrona con MCP: {str(e)}")
            return False

    def list_tools_sync(self) -> list[dict[str, Any]]:
        """
        Implementación puramente síncrona para listar herramientas.
        
        Returns:
            Lista de herramientas disponibles
        """
        try:
            if not self.initialized:
                success = self.initialize_sync()
                if not success:
                    return []

            # Usar requests directamente para obtener las herramientas
            # Intentar primero con /tools, luego con /mcp/v1/tools
            response = requests.get(f"{self.base_url}/tools", timeout=5)
            if response.status_code != 200:
                # Intentar ruta alternativa si la primera falla
                response = requests.get(f"{self.base_url}/mcp/v1/tools", timeout=5)
                if response.status_code != 200:
                    logger.error(f"Error al obtener herramientas MCP: {response.status_code}")
                    return []

            # Extraer las herramientas según el formato de respuesta
            if "tools" in response.json():
                tools = response.json().get("tools", [])
            else:
                # La respuesta podría ser directamente la lista de herramientas
                tools = response.json()

            logger.info(f"Obtenidas {len(tools)} herramientas del servidor MCP")
            return tools
        except Exception as e:
            logger.error(f"Error al listar herramientas MCP: {str(e)}")
            return []

    def call_tool_sync(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        Implementación puramente síncrona para llamar a una herramienta.
        
        Args:
            tool_name: Nombre de la herramienta a llamar
            params: Parámetros para la herramienta
            
        Returns:
            Resultado de la ejecución de la herramienta
        """
        try:
            if not self.initialized:
                success = self.initialize_sync()
                if not success:
                    return {"error": "No se pudo inicializar la conexión con el servidor MCP"}

            # Usar requests directamente para llamar a la herramienta
            # Intentar primero con la ruta principal /tools
            url = f"{self.base_url}/tools/{tool_name}"
            headers = {"Content-Type": "application/json"}

            try:
                response = requests.post(url, headers=headers, json=params, timeout=30)

                # Si falla, intentar con la ruta alternativa /mcp/v1/tools
                if response.status_code != 200:
                    alt_url = f"{self.base_url}/mcp/v1/tools/{tool_name}"
                    response = requests.post(alt_url, headers=headers, json=params, timeout=30)

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Herramienta MCP '{tool_name}' ejecutada exitosamente")
                    return result
                else:
                    error_msg = f"Error al llamar a {tool_name}: {response.status_code}"
                    if response.text:
                        error_msg += f" - {response.text}"
                    logger.error(error_msg)
                    return {"error": error_msg}
            except requests.exceptions.RequestException as req_error:
                logger.error(f"Error en la solicitud HTTP para {tool_name}: {str(req_error)}")
                return {"error": f"Error en la solicitud HTTP: {str(req_error)}"}
        except Exception as e:
            logger.error(f"Error al llamar a herramienta MCP {tool_name}: {str(e)}")
            return {"error": f"Error en la llamada a la herramienta: {str(e)}"}

    def close(self):
        """
        Cierra conexiones y finaliza el servidor MCP si fue iniciado por este cliente.
        """
        if self.mcp_process and self.mcp_process.poll() is None:
            logger.info(f"Cerrando servidor MCP con PID: {self.mcp_process.pid}")
            try:
                self.mcp_process.terminate()
                self.mcp_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("El servidor MCP no se cerró correctamente, forzando cierre")
                self.mcp_process.kill()

        self.initialized = False
        self.tools_cache = None

    async def initialize(self):
        """
        Inicializa la conexión y carga las herramientas disponibles.
        
        Esta función debe ser llamada antes de usar cualquier operación del cliente.
        """
        max_retries = 3
        retry_delay = 2.0  # segundos

        for attempt in range(1, max_retries + 1):
            try:
                if self.use_stdio:
                    # Usar transporte stdin/stdout
                    logger.info(f"Intento {attempt}/{max_retries} de conexión al servidor MCP vía stdio: {self.mcp_server_path}")

                    if not os.path.exists(self.mcp_server_path):
                        logger.error(f"No se encontró el archivo del servidor MCP en {self.mcp_server_path}")
                        return False

                    # Crear sesión de cliente stdio si no existe
                    if self._stdio_session is None:
                        self._stdio_session = StdioClientSession(self.mcp_server_path)

                    # Abrir la sesión
                    await self._stdio_session.open()

                    # Verificar la conexión obteniendo las herramientas
                    try:
                        tools = await asyncio.wait_for(self._stdio_session.list_tools(), timeout=5.0)
                        tool_count = len(tools)
                        logger.info(f"Conexión exitosa al servidor MCP vía stdio. Herramientas disponibles: {tool_count}")
                        return True
                    except TimeoutError:
                        logger.warning("Timeout al conectar con el servidor MCP vía stdio")
                        if attempt < max_retries:
                            logger.info(f"Reintentando en {retry_delay} segundos...")
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            logger.error(f"No se pudo conectar al servidor MCP después de {max_retries} intentos")
                            return False
                else:
                    # Usar transporte HTTP/SSE original
                    # Crear el cliente MultiServerMCP
                    self._client = MultiServerMCPClient({
                        "default": {
                            "transport": "sse",
                            "url": self.base_url,
                        }
                    })

                    # Intentar cargar herramientas para verificar la conexión
                    logger.info(f"Intento {attempt}/{max_retries} de conexión al servidor MCP en {self.base_url}")

                    # Intentar obtener herramientas con timeout para evitar bloqueos
                    try:
                        # En lugar de usar get_tools directamente, usamos list_tools_async
                        # que maneja correctamente los diferentes tipos de respuesta
                        tools = await asyncio.wait_for(self.list_tools_async(), timeout=5.0)

                        # Si llegamos aquí, la conexión fue exitosa
                        if tools:
                            tool_count = len(tools)
                            logger.info(f"Conexión exitosa al servidor MCP. Herramientas disponibles: {tool_count}")
                        else:
                            logger.warning("Conexión exitosa al servidor MCP, pero no se encontraron herramientas")

                        logger.info(f"Cliente MCP inicializado correctamente en {self.base_url}")
                        return True

                    except TimeoutError:
                        logger.warning(f"Timeout al conectar con el servidor MCP en {self.base_url}")
                        if attempt < max_retries:
                            logger.info(f"Reintentando en {retry_delay} segundos...")
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            logger.error(f"No se pudo conectar al servidor MCP después de {max_retries} intentos")
                            return False

            except Exception as e:
                logger.error(f"Error al inicializar cliente MCP: {str(e)}")
                if attempt < max_retries:
                    logger.info(f"Reintentando en {retry_delay} segundos...")
                    await asyncio.sleep(retry_delay)
                    continue
                return False

        # Si llegamos aquí, todos los intentos fallaron
        return False

    async def list_tools_async(self) -> list[dict[str, Any]]:
        """
        Lista las herramientas disponibles en el servidor MCP (versión asíncrona).
        
        Returns:
            Lista de herramientas disponibles con sus esquemas
        """
        if self._tools_cache is not None:
            return self._tools_cache

        try:
            if self.use_stdio:
                # Modo stdio
                if self._stdio_session is None:
                    success = await self.initialize()
                    if not success:
                        logger.error("No se pudo inicializar el cliente MCP (stdio)")
                        return []

                # Obtener herramientas mediante la sesión stdio
                self._tools_cache = await self._stdio_session.list_tools()
                logger.info(f"Herramientas MCP (stdio) cargadas: {len(self._tools_cache)}")
                return self._tools_cache
            else:
                # Modo HTTP/SSE original
                if self._client is None:
                    success = await self.initialize()
                    if not success:
                        logger.error("No se pudo inicializar el cliente MCP")
                        return []

                # Inicializar herramientas como lista vacía
                tools = []

                try:
                    # Manejar diferentes tipos de respuesta de get_tools
                    try:
                        # Verificar primero si el cliente tiene el método get_tools
                        if not hasattr(self._client, 'get_tools'):
                            logger.error("El cliente MCP no tiene el método get_tools")
                            return []

                        # Obtener el resultado de get_tools
                        get_tools_result = self._client.get_tools()

                        # Si es una lista, usarla directamente
                        if isinstance(get_tools_result, list):
                            tools = get_tools_result
                        # Si es una corutina, esperarla
                        elif hasattr(get_tools_result, '__await__'):
                            tools = await get_tools_result
                        # Otro tipo inesperado
                        else:
                            logger.warning(f"Tipo inesperado devuelto por get_tools: {type(get_tools_result)}")
                            return []

                    except Exception as e:
                        logger.error(f"Error al obtener herramientas del servidor MCP: {str(e)}")
                        return []

                    # Si no hay herramientas, devolver lista vacía
                    if not tools:
                        logger.warning("No se encontraron herramientas en el servidor MCP")
                        return []

                    # Convertir herramientas al formato esperado
                    self._tools_cache = []
                    for tool in tools:
                        try:
                            # Verificar que herramientas tienen la estructura esperada
                            if hasattr(tool, 'name') and hasattr(tool, 'description') and hasattr(tool, 'args'):
                                self._tools_cache.append({
                                    "name": tool.name,
                                    "description": tool.description,
                                    "inputs": {k: v for k, v in tool.args.items()},
                                    "outputs": {"result": {"type": "any", "description": "Resultado de la operación"}}
                                })
                            else:
                                logger.warning(f"Herramienta con formato inesperado: {tool}")
                        except Exception as e:
                            logger.error(f"Error al procesar herramienta: {str(e)}")

                    logger.info(f"Herramientas MCP cargadas: {len(self._tools_cache)}")
                    return self._tools_cache

                except (AttributeError, TypeError) as e:
                    logger.error(f"Error al acceder a las propiedades de las herramientas: {str(e)}")
                    return []

        except Exception as e:
            logger.error(f"Error al listar herramientas MCP: {str(e)}")
            return []

    def list_tools(self) -> list[dict[str, Any]]:
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

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
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

            if self.use_stdio:
                # Modo stdio
                if self._stdio_session is None:
                    success = await self.initialize()
                    if not success:
                        logger.error(f"No se pudo inicializar el cliente MCP (stdio) para llamar a la herramienta {tool_name}")
                        return {"error": "No se pudo inicializar la conexión con el servidor MCP"}

                # Llamar a la herramienta mediante la sesión stdio
                result = await self._stdio_session.call_tool(tool_name, params)

                # Registrar métricas
                execution_time = asyncio.get_event_loop().time() - start_time
                self.metrics.record_tool_execution(
                    tool_name=tool_name,
                    execution_time=execution_time,
                    status="success"
                )

                logger.info(f"Herramienta {tool_name} ejecutada vía stdio en {execution_time:.2f} segundos")
                return result
            else:
                # Modo HTTP/SSE original
                # Verificar si el cliente está inicializado
                if self._client is None:
                    success = await self.initialize()
                    if not success:
                        logger.error(f"No se pudo inicializar el cliente MCP para llamar a la herramienta {tool_name}")
                        return {"error": "No se pudo inicializar la conexión con el servidor MCP"}

                # Obtener herramientas disponibles - usando el método mejorado
                tools = await self.list_tools_async()
                if not tools:
                    logger.error("No hay herramientas disponibles en el servidor MCP")
                    return {"error": "No hay herramientas disponibles en el servidor MCP"}

                # Buscar la herramienta por nombre en la caché local
                tool_info = next((t for t in tools if t["name"] == tool_name), None)
                if not tool_info:
                    logger.error(f"Herramienta '{tool_name}' no encontrada en el servidor MCP")
                    return {"error": f"Herramienta '{tool_name}' no encontrada"}

                try:
                    # Intentar obtener la herramienta del cliente
                    mcp_tools = self._client.get_tools()

                    # Manejar diferentes tipos de respuesta
                    if hasattr(mcp_tools, '__await__'):
                        available_tools = await mcp_tools
                    else:
                        available_tools = mcp_tools

                    # Buscar la herramienta por nombre
                    tool = next((t for t in available_tools if t.name == tool_name), None)

                    if tool is None:
                        logger.error(f"Herramienta '{tool_name}' no disponible en el servidor")
                        return {"error": f"Herramienta '{tool_name}' no está disponible actualmente"}

                    # Ejecutar la herramienta
                    invoke_result = tool.ainvoke(params)

                    # Manejar diferentes tipos de respuesta
                    if hasattr(invoke_result, '__await__'):
                        result = await invoke_result
                    else:
                        result = invoke_result

                    # Calcular tiempo de ejecución
                    execution_time = asyncio.get_event_loop().time() - start_time

                    # Registrar métricas
                    self.metrics.record_execution(
                        service_name="mcp_client",
                        operation=tool_name,
                        execution_time=execution_time
                    )

                    logger.info(f"Herramienta MCP '{tool_name}' ejecutada exitosamente en {execution_time:.4f}s")

                    # Procesar el resultado según su tipo
                    if isinstance(result, tuple) and len(result) == 2:
                        content = result[0]
                        return {"result": content}
                    elif isinstance(result, dict):
                        # Ya es un diccionario, lo devolvemos directamente
                        return result
                    else:
                        # Para otros tipos, lo envolvemos en un diccionario
                        return {"result": result}

                except Exception as e:
                    logger.error(f"Error al ejecutar herramienta MCP '{tool_name}': {str(e)}")
                    self.metrics.record_error(
                        agent_name=f"mcp_client.{tool_name}",
                        error_type=str(e)
                    )
                    return {"error": f"Error al ejecutar herramienta: {str(e)}"}

        except Exception as e:
            # Registrar el error
            logger.error(f"Error al llamar a herramienta MCP {tool_name}: {str(e)}")
            self.metrics.record_error(
                agent_name=f"mcp_client.{tool_name}",
                error_type=str(e)
            )

            return {"error": f"Error en la llamada a la herramienta: {str(e)}"}

    async def invoke_tool(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        Alias para call_tool para mantener consistencia de nombres.
        """
        return await self.call_tool(tool_name, params)

    async def get_tool_wrapper(self, tool_name: str) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]] | None:
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
        async def tool_wrapper(params: dict[str, Any]) -> dict[str, Any]:
            return await self.call_tool(tool_name, params)

        return tool_wrapper

    async def close(self):
        """Cierra la conexión con el servidor MCP."""
        try:
            if self.use_stdio and self._stdio_session is not None:
                await self._stdio_session.close()
                self._stdio_session = None
                logger.info("Conexión stdio con servidor MCP cerrada correctamente")
            elif self._client is not None:
                # ¿Hay método de cierre en el cliente original?
                if hasattr(self._client, 'close') and callable(self._client.close):
                    close_method = self._client.close
                    # Verificar si es corutina o método normal
                    if asyncio.iscoroutinefunction(close_method):
                        await close_method()
                    else:
                        close_method()
                self._client = None
                logger.info("Conexión HTTP/SSE con servidor MCP cerrada correctamente")
        except Exception as e:
            logger.error(f"Error al cerrar cliente MCP: {str(e)}")

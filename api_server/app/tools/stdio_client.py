#!/usr/bin/env python3
"""
Cliente MCP utilizando StdioTransport.

Este módulo proporciona una implementación de transporte y cliente para
comunicarse con servidores MCP a través de entrada/salida estándar (stdio).
"""

import asyncio
import os
import sys
import json
import traceback
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, AsyncGenerator
from app.core.logging import logger

class StdioTransport:
    """
    Transporte para comunicarse con un servidor MCP a través de la entrada/salida estándar.
    
    Implementación basada en la documentación de MCP, permite interactuar con el servidor
    mediante un proceso hijo y comunicación por stdin/stdout.
    """
    
    def __init__(self, command: List[str]):
        """
        Inicializa el transporte.
        
        Args:
            command: Comando para iniciar el servidor MCP
        """
        self.command = command
        self.process = None
        
    async def __aenter__(self):
        """Inicia el proceso del servidor y configura los canales de comunicación."""
        # Iniciar el proceso del servidor
        logger.info(f"Iniciando proceso MCP con comando: {' '.join(self.command)}")
        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Leer mensajes de stderr en segundo plano
        asyncio.create_task(self._log_stderr())
        
        # Función para leer mensajes del servidor
        async def reader() -> AsyncGenerator[Dict[str, Any], None]:
            while True:
                if self.process.stdout:
                    line = await self.process.stdout.readline()
                    if not line:
                        break
                    try:
                        message = json.loads(line.decode('utf-8'))
                        logger.debug(f"Mensaje recibido: {str(message)[:100]}...")
                        yield message
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decodificando JSON: {line}, error: {str(e)}")
        
        # Función para enviar mensajes al servidor
        async def writer(message: Dict[str, Any]) -> None:
            if self.process.stdin:
                logger.debug(f"Enviando mensaje: {str(message)[:100]}...")
                data = json.dumps(message).encode('utf-8') + b'\n'
                self.process.stdin.write(data)
                await self.process.stdin.drain()
        
        return reader, writer
    
    async def _log_stderr(self):
        """Registra los mensajes de stderr del proceso."""
        if self.process and self.process.stderr:
            while True:
                line = await self.process.stderr.readline()
                if not line:
                    break
                logger.debug(f"MCP stderr: {line.decode('utf-8').strip()}")
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cierra el proceso del servidor."""
        if self.process:
            if self.process.stdin:
                self.process.stdin.close()
            
            try:
                # Terminar el proceso suavemente
                logger.info("Cerrando proceso MCP")
                self.process.terminate()
                # Esperar hasta que termine
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=3.0)
                except asyncio.TimeoutError:
                    # Si no termina a tiempo, forzar el cierre
                    logger.warning("Timeout al cerrar proceso MCP, forzando cierre")
                    self.process.kill()
                    await self.process.wait()
            except Exception as e:
                logger.error(f"Error al cerrar proceso MCP: {str(e)}")

class StdioClientSession:
    """
    Sesión del cliente para interactuar con un servidor MCP mediante StdioTransport.
    
    Implementación adaptada para ser compatible con el resto del sistema.
    """
    
    def __init__(self, mcp_server_path: str):
        """
        Inicializa la sesión del cliente.
        
        Args:
            mcp_server_path: Ruta al script del servidor MCP
        """
        self.mcp_server_path = mcp_server_path
        self.transport = StdioTransport(command=["python", mcp_server_path])
        self.reader = None
        self.writer = None
        self.request_id = 0
        self.pending_requests = {}
        self.read_task = None
        self._tools_cache = None
        
    async def open(self):
        """Abre la conexión con el servidor."""
        try:
            logger.info(f"Abriendo conexión MCP (StdioTransport) con servidor: {self.mcp_server_path}")
            self.reader, self.writer = await self.transport.__aenter__()
            # Iniciar la tarea de lectura
            self.read_task = asyncio.create_task(self._read_loop())
            logger.info("Sesión StdioClientSession abierta correctamente")
            return True
        except Exception as e:
            logger.error(f"Error al abrir sesión StdioClientSession: {str(e)}")
            return False
        
    async def _read_loop(self):
        """Bucle para leer y procesar mensajes del servidor."""
        try:
            async for message in self.reader():
                # Procesar mensajes del servidor
                logger.debug(f"Mensaje recibido del servidor MCP: {str(message)[:200]}...")
                if 'id' in message and message['id'] in self.pending_requests:
                    req_id = message['id']
                    future = self.pending_requests[req_id]
                    future.set_result(message)
                    del self.pending_requests[req_id]
                else:
                    logger.debug(f"Mensaje recibido sin ID correspondiente: {message}")
        except Exception as e:
            logger.error(f"Error en el bucle de lectura: {str(e)}")
            traceback.print_exc()
            
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Envía una solicitud al servidor y espera la respuesta.
        
        Args:
            method: Método a llamar
            params: Parámetros para el método
            
        Returns:
            Respuesta del servidor
        """
        self.request_id += 1
        req_id = str(self.request_id)
        
        # Crear la solicitud
        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {}
        }
        
        # Crear una future para esperar la respuesta
        future = asyncio.Future()
        self.pending_requests[req_id] = future
        
        try:
            # Enviar la solicitud
            logger.debug(f"Enviando solicitud al servidor MCP: {method}, ID: {req_id}")
            await self.writer(request)
            
            # Esperar la respuesta con timeout
            response = await asyncio.wait_for(future, timeout=30.0)
            logger.debug(f"Respuesta recibida para {method}, ID: {req_id}")
            
            # Verificar si hay error
            if "error" in response:
                error_msg = response.get("error", {})
                logger.error(f"Error del servidor MCP: {error_msg}")
                return {"error": f"Error del servidor: {error_msg}"}
                
            result = response.get("result", {})
            return result
        except asyncio.TimeoutError:
            logger.error(f"Timeout esperando respuesta para {method}, ID: {req_id}")
            # Eliminar la solicitud pendiente
            if req_id in self.pending_requests:
                del self.pending_requests[req_id]
            return {"error": "Timeout esperando respuesta del servidor"}
        except Exception as e:
            logger.error(f"Error al enviar solicitud {method}: {str(e)}")
            # Eliminar la solicitud pendiente
            if req_id in self.pending_requests:
                del self.pending_requests[req_id]
            return {"error": f"Error al comunicarse con el servidor: {str(e)}"}
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        Lista las herramientas disponibles en el servidor.
        
        Returns:
            Lista de herramientas disponibles
        """
        try:
            logger.info("Solicitando lista de herramientas al servidor MCP")
            response = await self._send_request("listTools")
            
            if "error" in response:
                logger.error(f"Error al listar herramientas: {response['error']}")
                return []
            
            tools = response.get("tools", [])
            
            # Formatear herramientas en formato común para compatibilidad
            formatted_tools = []
            for tool in tools:
                try:
                    args = tool.get("args", [])
                    inputs = {}
                    
                    for arg in args:
                        inputs[arg.get("name", "")] = {
                            "type": arg.get("type", "string"),
                            "description": arg.get("description", ""),
                            "required": arg.get("required", True)
                        }
                    
                    formatted_tools.append({
                        "name": tool.get("name", ""),
                        "description": tool.get("description", ""),
                        "inputs": inputs,
                        "outputs": {"result": {"type": "any", "description": "Resultado de la operación"}},
                        "args": args  # Mantener args original para compatibilidad
                    })
                except Exception as e:
                    logger.error(f"Error al formatear herramienta: {str(e)}")
            
            # Actualizar caché
            self._tools_cache = formatted_tools
            
            logger.info(f"Herramientas disponibles: {len(formatted_tools)}")
            for tool in formatted_tools:
                logger.debug(f"Herramienta: {tool['name']} - {tool['description']}")
            
            return formatted_tools
        except Exception as e:
            logger.error(f"Error al listar herramientas: {str(e)}")
            return []
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Llama a una herramienta específica en el servidor.
        
        Args:
            tool_name: Nombre de la herramienta
            params: Parámetros para la herramienta
            
        Returns:
            Resultado de la ejecución de la herramienta
        """
        try:
            logger.info(f"Llamando a herramienta MCP: {tool_name} con parámetros: {params}")
            start_time = asyncio.get_event_loop().time()
            
            response = await self._send_request("callTool", {
                "name": tool_name,
                "params": params
            })
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            if "error" in response:
                logger.error(f"Error al llamar a herramienta {tool_name}: {response['error']}")
                return {"error": response["error"], "success": False}
            
            logger.info(f"Herramienta {tool_name} ejecutada correctamente en {execution_time:.2f} segundos")
            response["execution_time"] = execution_time
            response["success"] = True
            
            return response
        except Exception as e:
            logger.error(f"Error al llamar a herramienta {tool_name}: {str(e)}")
            return {"error": str(e), "success": False}
    
    async def close(self):
        """Cierra la conexión con el servidor."""
        try:
            logger.info("Cerrando sesión StdioClientSession")
            # Cancelar la tarea de lectura
            if self.read_task:
                self.read_task.cancel()
                try:
                    await self.read_task
                except asyncio.CancelledError:
                    pass
            
            # Cerrar el transporte
            await self.transport.__aexit__(None, None, None)
            logger.info("Sesión StdioClientSession cerrada correctamente")
        except Exception as e:
            logger.error(f"Error al cerrar sesión StdioClientSession: {str(e)}")
        
    async def __aenter__(self):
        """Abre la conexión al entrar en el contexto."""
        await self.open()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cierra la conexión al salir del contexto."""
        await self.close() 
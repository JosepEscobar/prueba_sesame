"""
Módulo para integración de herramientas MCP con agentes.

Este módulo proporciona funciones para conectar agentes con herramientas MCP.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from app.core.logging import logger
from app.tools.mcp_client import MCPClient

# Mantener una referencia global al cliente MCP para reutilizarlo
_mcp_client = None

def get_mcp_tools_sync() -> List[Dict[str, Any]]:
    """
    Versión sincrónica para obtener herramientas MCP disponibles.
    
    Returns:
        Lista de herramientas MCP adaptadas para uso con LangChain
    """
    global _mcp_client
    
    try:
        # Deducir la ruta del servidor MCP relativa al proyecto
        import os
        from pathlib import Path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = Path(current_dir).parent.parent.parent.parent
        mcp_server_path = os.path.join(project_root, "mcp_server", "main.py")
        
        logger.info(f"Ruta MCP deducida: {mcp_server_path}")
        
        # Usar cliente global si existe, o crear uno nuevo
        if _mcp_client is None:
            logger.info("Creando nuevo cliente MCP global")
            _mcp_client = MCPClient(
                base_url="http://localhost:4500",
                use_stdio=False,  # No usar stdio para evitar problemas con loop de eventos
                mcp_server_path=mcp_server_path
            )
        
        # Inicializar de manera sincrónica y obtener herramientas
        success = _mcp_client.initialize_sync()
        
        if not success:
            logger.error("No se pudo inicializar el cliente MCP")
            return []
            
        # Obtener las herramientas usando la versión sincrónica
        tools = _mcp_client.list_tools_sync()
        
        # Convertir herramientas a formato para LangChain
        langchain_tools = []
        for tool in tools:
            # Crear funciones closures para cada herramienta
            tool_name = tool["name"]
            
            def create_tool_function(tool_name):
                def tool_function(**kwargs):
                    # Usar el cliente global
                    global _mcp_client
                    if _mcp_client is None:
                        logger.error(f"Error: cliente MCP no disponible para herramienta {tool_name}")
                        return {"error": "Cliente MCP no inicializado"}
                    return _mcp_client.call_tool_sync(tool_name, kwargs)
                return tool_function
                
            langchain_tools.append({
                "name": tool_name,
                "description": tool.get("description", f"Herramienta {tool_name} del servidor MCP"),
                "func": create_tool_function(tool_name)
            })
        
        logger.info(f"Herramientas MCP cargadas: {len(langchain_tools)}")
        return langchain_tools
        
    except Exception as e:
        logger.error(f"Error al cargar herramientas MCP: {str(e)}")
        return []

async def get_mcp_tools() -> List[Dict[str, Any]]:
    """
    Obtiene herramientas MCP disponibles y las convierte a formato para LangChain.
    
    Returns:
        Lista de herramientas MCP adaptadas para uso con LangChain
    """
    return get_mcp_tools_sync()

def configure_agent_with_mcp(agent, tools):
    """
    Configura un agente con herramientas MCP.
    
    Args:
        agent: El agente a configurar
        tools: Lista de herramientas a añadir
    """
    try:
        # Verificar que tools sea una lista
        if not isinstance(tools, list):
            logger.warning(f"Las herramientas MCP no son una lista. Tipo recibido: {type(tools)}")
            # Si es un diccionario, intentar convertirlo a lista
            if isinstance(tools, dict):
                tools_list = []
                for name, tool_data in tools.items():
                    if isinstance(tool_data, dict) and 'func' in tool_data:
                        tools_list.append(tool_data)
                    else:
                        tools_list.append({
                            "name": name,
                            "description": str(tool_data),
                            "func": lambda **kwargs: {"error": "Herramienta no disponible"}
                        })
                tools = tools_list
                logger.info(f"Convertidas {len(tools)} herramientas de diccionario a lista")
            else:
                # No podemos hacer nada con este formato
                logger.error("No se puede procesar el formato de herramientas proporcionado")
                return
        
        # Ahora configurar el agente con la lista de herramientas
        if hasattr(agent, "tools"):
            if isinstance(agent.tools, list):
                agent.tools.extend(tools)
                logger.info(f"Añadidas {len(tools)} herramientas MCP al agente")
            elif isinstance(agent.tools, dict):
                # Si agent.tools es un diccionario, añadir las herramientas como entradas
                for tool in tools:
                    agent.tools[tool["name"]] = tool
                logger.info(f"Añadidas {len(tools)} herramientas MCP al diccionario del agente")
            else:
                logger.warning(f"Formato de agent.tools no soportado: {type(agent.tools)}")
        else:
            logger.warning("El agente no tiene un atributo 'tools' compatible")
            
    except Exception as e:
        logger.error(f"Error al configurar agente con herramientas MCP: {str(e)}") 
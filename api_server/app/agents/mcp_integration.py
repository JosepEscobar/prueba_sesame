"""
Módulo de integración de Model Context Protocol (MCP) para agentes.

Este módulo sigue el patrón oficial de integración de MCP con LangChain y LangGraph.
"""

from typing import List, Dict, Any, Optional
import os
from pathlib import Path

from app.core.logging import logger
from app.core.config import get_settings
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

settings = get_settings()

def get_mcp_client() -> MultiServerMCPClient:
    """
    Obtiene un cliente MCP configurado según la documentación oficial.
    
    Returns:
        Cliente MCP con servidores configurados
    """
    # Configuración de servidor MCP siguiendo el patrón oficial
    client = MultiServerMCPClient({
        "sesame": {
            "transport": "sse",
            "url": settings.MCP_CLIENT_URL,
        },
        # Se pueden configurar servidores adicionales si es necesario
        # "filesystem": {
        #     "command": "npx",
        #     "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
        # },
        # "postgres": {
        #     "command": "npx",
        #     "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/mydb"]
        # }
    })
    
    return client

def get_mcp_tools():
    """
    Obtiene herramientas MCP adaptadas para usar con LangChain/LangGraph.
    
    Returns:
        Lista de herramientas adaptadas para LangChain
    """
    try:
        client = get_mcp_client()
        tools = load_mcp_tools(client)
        logger.info(f"Se cargaron {len(tools)} herramientas MCP")
        for tool in tools:
            logger.info(f"Herramienta MCP cargada: {tool.name}")
        return tools
    except Exception as e:
        logger.error(f"Error al cargar herramientas MCP: {str(e)}")
        return []

def configure_agent_with_mcp(agent, tools_list=None):
    """
    Configura un agente con herramientas MCP según la documentación oficial.
    
    Args:
        agent: El agente a configurar
        tools_list: Lista opcional de herramientas MCP preconfiguradas
    
    Returns:
        Agente configurado con herramientas MCP
    """
    if tools_list is None:
        tools_list = get_mcp_tools()
    
    # Añadir herramientas al agente
    if hasattr(agent, 'tools') and isinstance(agent.tools, list):
        agent.tools.extend(tools_list)
        logger.info(f"Se añadieron {len(tools_list)} herramientas MCP al agente")
    else:
        logger.warning("No se pudieron añadir herramientas MCP al agente (no tiene atributo 'tools' compatible)")
    
    return agent 
"""
Script para registrar todas las implementaciones de herramientas en el sistema.
"""

import asyncio
from pathlib import Path

from app.core.logging import logger
from app.tools.tool_registry import tool_registry
from app.tools.implementations import FinancialModelsImplementation
from app.tools.mcp_client_official import MCPClientOfficial

def register_all_tools():
    """
    Registra todas las implementaciones de herramientas disponibles en el sistema.
    
    Esta función debe ser llamada durante la inicialización de la aplicación
    para asegurar que todas las herramientas estén disponibles para los agentes.
    """
    logger.info("Iniciando registro de implementaciones de herramientas...")
    
    # Registrar implementación de financial_models
    financial_models_impl = FinancialModelsImplementation()
    success = tool_registry.register_tool_implementation(
        "financial_models", 
        financial_models_impl.get_models
    )
    if success:
        logger.info("Implementación de financial_models registrada correctamente")
    else:
        logger.warning("No se pudo registrar la implementación de financial_models")
    
    # Registrar cliente MCP para otras herramientas
    asyncio.create_task(_register_mcp_tools())
    
    # Mostrar resumen de herramientas registradas
    all_tools = tool_registry.list_tools()
    implemented_tools = tool_registry.list_tools_with_implementations()
    
    logger.info(f"Registro de herramientas completado:")
    logger.info(f"  - Total de herramientas definidas: {len(all_tools)}")
    logger.info(f"  - Herramientas con implementación: {len(implemented_tools)}")
    logger.info(f"  - Herramientas pendientes: {len(all_tools) - len(implemented_tools)}")
    
    return {
        "total_tools": len(all_tools),
        "implemented_tools": len(implemented_tools),
        "pending_tools": len(all_tools) - len(implemented_tools)
    }

async def _register_mcp_tools():
    """
    Registra herramientas disponibles a través del cliente MCP.
    
    Esta función asíncrona se ejecuta en segundo plano para no bloquear
    la inicialización de la aplicación.
    """
    try:
        # Inicializar el cliente MCP oficial
        mcp_client = MCPClientOfficial()
        initialized = await mcp_client.initialize()
        
        if not initialized:
            logger.warning("No se pudo inicializar el cliente MCP, las herramientas MCP no estarán disponibles")
            return
        
        # Registrar las herramientas disponibles en el servidor MCP
        tools = await mcp_client.list_tools()
        logger.info(f"Herramientas disponibles en el servidor MCP: {len(tools)}")
        
        for tool in tools:
            tool_name = tool["name"]
            
            # Obtener un wrapper para la herramienta
            wrapper = await mcp_client.get_tool_wrapper(tool_name)
            if wrapper:
                # Registrar la herramienta con el wrapper
                success = tool_registry.register_tool_implementation(tool_name, wrapper)
                if success:
                    logger.info(f"Implementación de {tool_name} registrada correctamente (via MCP oficial)")
                else:
                    logger.warning(f"No se pudo registrar la implementación de {tool_name}")
    
    except Exception as e:
        logger.error(f"Error al registrar herramientas MCP: {str(e)}") 
"""
Script para registrar todas las implementaciones de herramientas en el sistema.
"""

from app.core.logging import logger
from app.tools.tool_registry import tool_registry
from app.tools.implementations import FinancialModelsImplementation
from app.tools.mcp_client import MCPClient

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
    mcp_client = MCPClient()
    
    # Registrar implementación para query_kb a través del cliente MCP
    async def query_kb_wrapper(params):
        return await mcp_client.call_tool("query_kb", params)
    
    success = tool_registry.register_tool_implementation("query_kb", query_kb_wrapper)
    if success:
        logger.info("Implementación de query_kb registrada correctamente (via MCP)")
    else:
        logger.warning("No se pudo registrar la implementación de query_kb")
    
    # Registrar implementación para search_articles a través del cliente MCP
    async def search_articles_wrapper(params):
        return await mcp_client.call_tool("search_articles", params)
    
    success = tool_registry.register_tool_implementation("search_articles", search_articles_wrapper)
    if success:
        logger.info("Implementación de search_articles registrada correctamente (via MCP)")
    else:
        logger.warning("No se pudo registrar la implementación de search_articles")
    
    # Registrar herramientas adicionales aquí cuando se implementen
    
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
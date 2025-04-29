import asyncio
import os
import sys
from pathlib import Path
import argparse

from app.core.logging import logger
from app.tools.server.mcp_server import MCPToolServer, run_server

async def init_mcp_server(host: str = "localhost", port: int = 4000) -> MCPToolServer:
    """
    Inicializa y configura un servidor MCP con las herramientas disponibles.
    
    Args:
        host: Host en el que se ejecutará el servidor
        port: Puerto en el que se ejecutará el servidor
        
    Returns:
        Instancia del servidor MCP configurado
    """
    # Crear el servidor MCP
    server = MCPToolServer(host=host, port=port)
    
    # Cargar esquemas desde el directorio de esquemas
    schemas_dir = Path(__file__).parent.parent / "schemas"
    server.register_tools_from_directory(schemas_dir)
    
    # Registrar implementación de financial_models
    from app.tools.server.financial_models_impl import FinancialModelsMCPTool
    financial_models_tool = FinancialModelsMCPTool(
        schema_path=str(schemas_dir / "financial_models.json")
    )
    server.register_tool_implementation(
        "financial_models", 
        financial_models_tool.execute
    )
    
    # Agregar implementaciones para otras herramientas aquí
    
    return server

async def main():
    """Punto de entrada principal para iniciar el servidor MCP."""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Servidor MCP para herramientas locales")
    parser.add_argument("--host", default="localhost", help="Host para el servidor MCP")
    parser.add_argument("--port", type=int, default=4000, help="Puerto para el servidor MCP")
    args = parser.parse_args()
    
    # Inicializar el servidor
    server = await init_mcp_server(host=args.host, port=args.port)
    
    # Ejecutar el servidor
    await run_server(server)

if __name__ == "__main__":
    # Ejecutar el bucle de eventos
    asyncio.run(main()) 
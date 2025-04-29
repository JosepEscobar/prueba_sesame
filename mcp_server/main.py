#!/usr/bin/env python3
"""
Script principal para iniciar el servidor MCP.

Este servidor expone herramientas locales a través del protocolo MCP (Model Context Protocol)
para que puedan ser consumidas por clientes como LangChain, LlamaIndex u otros agentes.
"""

import os
import sys
import logging
import argparse
import asyncio
from pathlib import Path

# Añadir el directorio raíz al path para poder importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from app.core.logging import setup_logging
from app.tools.server.mcp_server import MCPToolServer, run_server

# Configurar logging
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)
setup_logging()

logger = logging.getLogger("mcp_server")

async def main():
    """Punto de entrada principal para iniciar el servidor MCP."""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Servidor MCP para herramientas locales")
    parser.add_argument("--host", default="0.0.0.0", help="Host para el servidor MCP (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=4000, help="Puerto para el servidor MCP (default: 4000)")
    args = parser.parse_args()
    
    # Inicializar el servidor
    server = MCPToolServer(host=args.host, port=args.port)
    
    # Cargar herramientas desde el directorio de esquemas
    schemas_dir = Path(__file__).parent / "app" / "tools" / "schemas"
    server.register_tools_from_directory(schemas_dir)
    
    # Registrar implementaciones
    try:
        # Implementación de financial_models
        from app.tools.implementations.financial_models import FinancialModelsImplementation
        financial_models_impl = FinancialModelsImplementation()
        server.register_tool_implementation("financial_models", financial_models_impl.execute)
        logger.info("Herramienta financial_models registrada correctamente")
        
        # Implementación de data_lookup
        from app.tools.implementations.data_lookup import DataLookupImplementation
        data_lookup_impl = DataLookupImplementation()
        server.register_tool_implementation("data_lookup", data_lookup_impl.execute)
        logger.info("Herramienta data_lookup registrada correctamente")
        
        # Añadir más implementaciones aquí si es necesario
        
    except Exception as e:
        logger.error(f"Error al registrar implementaciones: {str(e)}")
    
    # Ejecutar el servidor
    await run_server(server)

if __name__ == "__main__":
    try:
        logger.info("Iniciando servidor MCP")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Servidor MCP detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal en el servidor MCP: {str(e)}")
        sys.exit(1) 
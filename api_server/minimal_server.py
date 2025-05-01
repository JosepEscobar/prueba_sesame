#!/usr/bin/env python3
"""
Servidor API mínimo que verifica la conexión con el servidor MCP.
"""

from fastapi import FastAPI
import uvicorn
import logging

from app.agents.mcp_integration import get_mcp_tools, get_mcp_client

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("minimal_server")

app = FastAPI(title="Minimal MCP Test Server")

@app.get("/")
async def root():
    """Ruta raíz del servidor."""
    return {
        "message": "Minimal MCP Test Server",
        "status": "running"
    }

@app.get("/mcp-status")
async def mcp_status():
    """Verificar el estado de la conexión al servidor MCP."""
    try:
        client = get_mcp_client()
        tools = get_mcp_tools()
        
        tool_names = [tool.name for tool in tools] if tools else []
        
        return {
            "connection": "success" if len(tool_names) > 0 else "partial",
            "tools_count": len(tool_names),
            "available_tools": tool_names
        }
    except Exception as e:
        logger.error(f"Error al conectar con el servidor MCP: {str(e)}")
        return {
            "connection": "failed",
            "error": str(e)
        }

if __name__ == "__main__":
    logger.info("Iniciando servidor mínimo para pruebas MCP")
    uvicorn.run(app, host="0.0.0.0", port=8001) 
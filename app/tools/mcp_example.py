#!/usr/bin/env python
"""
Script de ejemplo para probar el cliente MCP.

Este script muestra cómo utilizar el cliente MCP oficial para:
1. Listar herramientas disponibles
2. Llamar a una herramienta específica
3. Manejar errores

Uso:
    python -m app.tools.mcp_example
"""

import asyncio
import argparse
import json
from typing import Dict, Any, List, Optional

from app.tools.mcp_client_official import MCPClientOfficial
from app.core.config import get_settings

async def list_tools(client: MCPClientOfficial) -> List[Dict[str, Any]]:
    """
    Lista las herramientas disponibles en el servidor MCP.
    
    Args:
        client: Cliente MCP inicializado
        
    Returns:
        Lista de herramientas disponibles
    """
    return await client.list_tools()

async def call_tool(client: MCPClientOfficial, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Llama a una herramienta específica en el servidor MCP.
    
    Args:
        client: Cliente MCP inicializado
        tool_name: Nombre de la herramienta a llamar
        params: Parámetros para la herramienta
        
    Returns:
        Resultado de la llamada a la herramienta
    """
    return await client.call_tool(tool_name, params)

async def main():
    """Función principal del script de ejemplo."""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Ejemplo de uso del cliente MCP")
    parser.add_argument("--url", help="URL del servidor MCP")
    parser.add_argument("--tool", help="Herramienta a ejecutar")
    parser.add_argument("--params", help="Parámetros para la herramienta (formato JSON)")
    args = parser.parse_args()
    
    # Configuración
    settings = get_settings()
    
    # Inicializar el cliente MCP
    client = MCPClientOfficial(
        base_url=args.url if args.url else settings.MCP_CLIENT_URL
    )
    
    # Inicializar el cliente
    initialized = await client.initialize()
    if not initialized:
        print("No se pudo inicializar el cliente MCP")
        return
    
    # Si no se especifica una herramienta, mostrar la lista de herramientas disponibles
    if not args.tool:
        print("Herramientas disponibles:")
        try:
            tools = await list_tools(client)
            for i, tool in enumerate(tools, 1):
                print(f"{i}. {tool['name']}: {tool['description']}")
        except Exception as e:
            print(f"Error al listar herramientas: {str(e)}")
        return
    
    # Si se especifica una herramienta, llamarla con los parámetros proporcionados
    tool_name = args.tool
    try:
        # Parsear parámetros si se proporcionan
        params = {}
        if args.params:
            try:
                params = json.loads(args.params)
            except json.JSONDecodeError:
                print(f"Error al parsear parámetros JSON: {args.params}")
                return
        
        # Ejemplo básico si no se proporcionan parámetros
        if not params and tool_name == "financial_models":
            params = {"model_type": "cash_flow"}
        elif not params and tool_name == "query_kb":
            params = {"query": "inteligencia artificial", "kb_name": "general"}
        elif not params and tool_name == "search_articles":
            params = {"query": "machine learning"}
        
        print(f"Llamando a herramienta '{tool_name}' con parámetros:")
        print(json.dumps(params, indent=2, ensure_ascii=False))
        
        # Llamar a la herramienta
        result = await call_tool(client, tool_name, params)
        
        # Mostrar el resultado
        print("\nResultado:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error al llamar a la herramienta {tool_name}: {str(e)}")
    
    # Cerrar el cliente MCP
    await client.close()

if __name__ == "__main__":
    asyncio.run(main()) 
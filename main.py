#!/usr/bin/env python3
"""
Script principal para iniciar el cliente MCP Sesame.

Este script facilita la ejecución del cliente desde la línea de comandos.
"""

import os
import sys

# Asegurar que el directorio actual está en el path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar la función principal del cliente
from cliente_mcp_sesame import main

if __name__ == "__main__":
    sys.exit(main())


def main():
    """Inicia el servidor MCP."""
    # Verificar puerto disponible
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "4000"))


# Función de inicio del servidor
def iniciar_servidor():
    """Inicia el servidor MCP."""
    # Verificar puerto disponible
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "4000"))

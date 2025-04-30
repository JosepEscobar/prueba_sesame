#!/usr/bin/env python3
"""
Script principal para iniciar el cliente MCP Sesame.

Este script facilita la ejecución del cliente desde la línea de comandos.
"""

import sys
import os
from pathlib import Path

# Asegurar que el directorio actual está en el path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar la función principal del cliente
from cliente_mcp_sesame import main

if __name__ == "__main__":
    sys.exit(main()) 
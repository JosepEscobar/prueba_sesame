#!/usr/bin/env python
"""
Script para ejecutar la aplicación en desarrollo.
Configura uvicorn con opciones para desarrollo local.
"""

import uvicorn
import argparse
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def main():
    """Función principal para ejecutar el servidor."""
    parser = argparse.ArgumentParser(description="Ejecutar el servidor Multi-Agent System")
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host para escuchar (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Puerto para escuchar (default: 8000)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Habilitar recarga automática"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Número de workers (default: 1)"
    )
    
    args = parser.parse_args()
    
    # Configurar el servidor uvicorn
    uvicorn_config = {
        "app": "app.main:app",
        "host": args.host,
        "port": args.port,
        "reload": args.reload,
        "workers": args.workers,
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
    }
    
    print(f"Iniciando servidor en http://{args.host}:{args.port}")
    print(f"Modo recarga: {'Activado' if args.reload else 'Desactivado'}")
    print(f"Documentación disponible en http://{args.host}:{args.port}/docs")
    
    uvicorn.run(**uvicorn_config)

if __name__ == "__main__":
    main() 
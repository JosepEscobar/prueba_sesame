#!/usr/bin/env python3
"""
API principal del sistema.

Esta API proporciona puntos finales para interactuar con los agentes del sistema
de asistencia empresarial.
"""

import os
import sys
import logging
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Añadir el directorio raíz al path para poder importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from app.core.logging import setup_logging
from app.core.config import get_settings
from app.api.routes import router

# Configurar logging
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)
setup_logging()

logger = logging.getLogger("api_server")
settings = get_settings()

# Crear la aplicación FastAPI
app = FastAPI(
    title="Sesame API",
    description="API para el sistema de asistencia empresarial Sesame",
    version="0.1.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas de la API
app.include_router(router, prefix=settings.API_PREFIX)

@app.get("/")
async def root():
    """Ruta raíz de la API."""
    return {
        "message": "¡Bienvenido a la API de Sesame!",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Verificar el estado de la API."""
    return {
        "status": "healthy",
        "version": "0.1.0"
    }

if __name__ == "__main__":
    # Ejecutar la aplicación con uvicorn
    logger.info("Iniciando servidor API")
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 
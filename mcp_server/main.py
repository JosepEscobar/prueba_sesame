#!/usr/bin/env python3
"""
Script principal para iniciar el servidor MCP.

Este servidor expone herramientas locales a través del protocolo MCP (Model Context Protocol)
para que puedan ser consumidas por clientes como LangChain, LlamaIndex u otros agentes.
"""

import os
import sys
from pathlib import Path
import uvicorn
from fastapi import FastAPI

# Crear la aplicación FastAPI
app = FastAPI(
    title="Servidor MCP",
    description="Servidor para exponer herramientas locales mediante MCP",
    version="0.1.0"
)

@app.get("/")
async def root():
    """Ruta raíz del servidor."""
    return {
        "message": "¡Bienvenido al servidor MCP de Sesame!",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Verificar el estado del servidor."""
    return {
        "status": "healthy",
        "version": "0.1.0"
    }

if __name__ == "__main__":
    # Ejecutar la aplicación con uvicorn
    print("Iniciando servidor simple para prueba...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=4000,
        log_level="info"
    ) 
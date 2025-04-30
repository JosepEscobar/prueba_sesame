#!/usr/bin/env python3
"""
Script de prueba para verificar la carga de variables de entorno en RouterAgent.

Este script intenta inicializar el RouterAgent y verificar que las variables de
entorno se cargan correctamente.
"""

import os
import sys
import json
from pathlib import Path

# Añadir el directorio actual al path de Python
sys.path.insert(0, '.')

# Importar después de configurar el path
from app.core.config import get_settings
from app.core.logging import logger
from app.agents.router_agent import RouterAgent, load_api_credentials


def test_env_variables():
    """Prueba la carga de variables de entorno y la inicialización del agente."""
    print("\n=== Prueba de Variables de Entorno ===\n")
    
    # Cargar configuración
    settings = get_settings()
    print(f"APP_NAME: {settings.APP_NAME}")
    print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"OPENAI_MODEL: {settings.OPENAI_MODEL}")
    
    # Verificar API key (sólo mostrar si existe, no el valor real)
    api_key_status = "CONFIGURADA" if settings.is_openai_api_key_valid() else "NO CONFIGURADA"
    print(f"OPENAI_API_KEY: {api_key_status}")
    
    # Comprobar proxies
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    print(f"HTTP_PROXY: {'CONFIGURADO' if http_proxy else 'NO CONFIGURADO'}")
    print(f"HTTPS_PROXY: {'CONFIGURADO' if https_proxy else 'NO CONFIGURADO'}")
    
    print("\n=== Carga de Credenciales ===\n")
    
    # Probar la función de carga de credenciales
    api_key, has_valid_key = load_api_credentials()
    print(f"¿API key válida? {has_valid_key}")
    
    # Verificar proxies configurados en el entorno
    http_proxy = os.environ.get("http_proxy")
    https_proxy = os.environ.get("https_proxy")
    tiene_proxies = bool(http_proxy or https_proxy)
    print(f"¿Hay proxies configurados? {'Sí' if tiene_proxies else 'No'}")
    
    print("\n=== Inicialización del RouterAgent ===\n")
    
    # Intentar inicializar el RouterAgent
    agent = RouterAgent()
    print(f"¿Agente inicializado? {'Sí' if agent else 'No'}")
    print(f"¿OpenAI disponible? {agent.has_openai}")
    print(f"¿Cliente OpenAI directo? {'Sí' if agent.client else 'No'}")
    print(f"¿LLM configurado? {'Sí' if agent.llm else 'No'}")
    if agent.llm:
        print(f"Tipo de LLM: {type(agent.llm).__name__}")
    
    print("\n=== Prueba de Clasificación ===\n")
    
    # Probar clasificación por keywords (siempre disponible)
    queries = [
        "Analiza los resultados financieros del último trimestre",
        "Evalúa el rendimiento de nuestra campaña de marketing en redes sociales",
        "Predice la tendencia de ventas para los próximos 6 meses"
    ]
    
    for query in queries:
        agent_type = agent._classify_query_by_keywords(query)
        print(f"Consulta: '{query}'")
        print(f"Clasificación: {agent_type}\n")
    
    print("=== Prueba Completada ===\n")


if __name__ == "__main__":
    test_env_variables() 
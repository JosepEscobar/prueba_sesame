"""
Implementaciones de herramientas para el servidor MCP.

Este módulo proporciona las implementaciones concretas de las herramientas
que serán expuestas a través del servidor MCP.
"""

from app.tools.implementations.data_lookup import buscar_datos_financieros, data_lookup
from app.tools.implementations.financial_models import (
    analizar_rendimiento_campania,
    analizar_tendencia,
    calcular_ratios_financieros,
    financial_models,
    predecir_valores,
    recomendar_estrategia_marketing,
)
from app.tools.implementations.search_articles import search_articles

# Lista de todas las herramientas disponibles para su registro automático
AVAILABLE_TOOLS = [
    buscar_datos_financieros,
    data_lookup,
    calcular_ratios_financieros,
    recomendar_estrategia_marketing,
    analizar_tendencia,
    predecir_valores,
    search_articles,
    financial_models,
    analizar_rendimiento_campania
]

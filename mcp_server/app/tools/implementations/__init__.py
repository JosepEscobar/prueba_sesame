"""
Implementaciones de herramientas para el servidor MCP.

Este módulo proporciona las implementaciones concretas de las herramientas
que serán expuestas a través del servidor MCP.
"""

from mcp_server.app.tools.implementations.data_lookup import (
    buscar_datos_financieros,
    data_lookup
)

from mcp_server.app.tools.implementations.financial_models import (
    calcular_ratios_financieros,
    recomendar_estrategia_marketing,
    analizar_tendencia,
    predecir_valores
)

# Lista de todas las herramientas disponibles para su registro automático
AVAILABLE_TOOLS = [
    buscar_datos_financieros,
    data_lookup,
    calcular_ratios_financieros,
    recomendar_estrategia_marketing,
    analizar_tendencia, 
    predecir_valores
] 
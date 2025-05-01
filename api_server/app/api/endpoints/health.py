#!/usr/bin/env python3
"""
Controlador para health check del API.

Este módulo proporciona funciones para verificar el estado de salud del servicio
API y sus dependencias, especialmente la conexión con el servidor MCP.
"""

import os
from typing import Any

from app.core.logging import logger
from app.tools.mcp_client import MCPClient

# Obtener la URL del servidor MCP de las variables de entorno
mcp_url = os.environ.get("MCP_SERVER_URL", "http://localhost:4000")


class HealthController:
    """
    Controlador para verificar el estado de salud del servicio API.

    Este controlador comprueba la disponibilidad y funcionalidad de los
    componentes críticos del sistema, incluyendo la conexión con el servidor MCP.
    """

    @staticmethod
    def check_mcp_status() -> dict[str, Any]:
        """
        Verifica el estado de la conexión con el servidor MCP.

        Returns:
            Dict con el estado de la conexión MCP y detalles adicionales
        """
        try:
            # Crear un cliente MCP para verificar la conexión
            mcp_client = MCPClient(base_url=mcp_url)
            mcp_connection_ok = mcp_client.initialize_sync()

            # Comprobar si hay herramientas disponibles
            tools: list[dict[str, Any]] = []
            if mcp_connection_ok:
                tools = mcp_client.list_tools_sync()

                if tools and len(tools) > 0:
                    mcp_status = "connected"
                    logger.info(f"MCP conectado correctamente con {len(tools)} herramientas disponibles")
                else:
                    mcp_status = "degraded"
                    logger.warning("MCP conectado pero sin herramientas disponibles")
            else:
                mcp_status = "disconnected"
                logger.warning("No se pudo conectar con el servidor MCP")

        except Exception as e:
            # Si hay cualquier error al conectar con MCP
            mcp_status = "disconnected"
            tools = []
            logger.error(f"Error al verificar estado de MCP: {str(e)}")

        return {"mcp_status": mcp_status, "mcp_url": mcp_url, "tools_available": len(tools) if tools else 0}

    @staticmethod
    def check_system_health() -> dict[str, Any]:
        """
        Realiza un health check completo del sistema.

        Verifica todos los componentes críticos y determina el estado
        general del sistema.

        Returns:
            Dict con el estado completo del sistema
        """
        # Verificar estado del servidor MCP
        mcp_status_info = HealthController.check_mcp_status()
        mcp_status = mcp_status_info["mcp_status"]

        # Determinar el estado general del sistema basado en los componentes
        system_status = "healthy"

        # Si MCP no está funcionando correctamente, el sistema está degradado
        if mcp_status != "connected":
            system_status = "degraded"

        # Combinar toda la información de estado
        return {
            "status": system_status,
            "version": "0.1.0",
            "mcp_status": mcp_status,
            "components": {"mcp": mcp_status_info},
        }


# Crear una instancia global del controlador
health_controller = HealthController()

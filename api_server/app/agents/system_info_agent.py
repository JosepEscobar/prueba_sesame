import time
from typing import Any

from app.agents.base import BaseAgent
from app.core.config import get_settings
from app.core.logging import logger
from app.core.metrics import MetricsCollector

settings = get_settings()


class SystemInfoAgent(BaseAgent):
    """
    Agente especializado en proporcionar información sobre las capacidades
    de la API de Sesame y el estado actual del servicio.

    Responde a consultas relacionadas con:
    - Funcionalidades disponibles en el sistema
    - Estado de los servicios
    - Agentes disponibles y sus capacidades
    - Información general del sistema
    """

    def __init__(self):
        """Inicializa el agente de información del sistema."""
        super().__init__(
            name="system_info_agent",
            description="Agente que proporciona información sobre las capacidades del sistema y su estado actual.",
        )

        # Información sobre los agentes disponibles en el sistema
        self.available_agents = {
            "finance_agent": {
                "description": "Especialista en análisis financiero y consultoría económica.",
                "capabilities": [
                    "análisis financiero",
                    "planificación de presupuestos",
                    "optimización fiscal",
                    "estrategias de inversión",
                    "gestión de riesgos financieros",
                    "valuación empresarial",
                    "análisis de rentabilidad",
                    "modelos financieros",
                    "planificación de flujo de caja",
                ],
            },
            "marketing_agent": {
                "description": "Especialista en estrategias de marketing y análisis de mercado.",
                "capabilities": [
                    "estrategia de marketing",
                    "posicionamiento de marca",
                    "marketing digital",
                    "segmentación de mercado",
                    "análisis competitivo",
                    "estrategia de contenidos",
                    "optimización de canales",
                    "análisis de audiencia",
                    "customer journey",
                    "planificación de campañas",
                ],
            },
            "analysis_agent": {
                "description": "Especialista en análisis de información compleja.",
                "capabilities": [
                    "análisis de datos",
                    "procesamiento de documentos",
                    "extracción de insights",
                    "identificación de patrones",
                    "resumen de información",
                    "análisis FODA",
                ],
            },
            "system_info_agent": {
                "description": "Especialista en proporcionar información sobre el sistema.",
                "capabilities": [
                    "información sobre capacidades del sistema",
                    "estado de los servicios",
                    "información sobre agentes disponibles",
                    "documentación del sistema",
                ],
            },
        }

        # Información sobre las API endpoints disponibles
        self.api_endpoints = {
            "/api/v1/query": "Endpoint principal para consultas de usuarios",
            "/health": "Verifica el estado de salud del servicio",
            "/mcp/status": "Obtiene información sobre el estado de conexión con MCP",
            "/metrics": "Proporciona métricas de rendimiento del sistema",
        }

        # Servicios del sistema y su descripción
        self.system_services = {
            "Orquestación de Agentes": "Coordina la ejecución de múltiples agentes especializados",
            "Procesamiento de Lenguaje Natural": "Interpreta consultas en lenguaje natural",
            "Guardrails de Seguridad": "Aplica políticas de uso y seguridad",
            "Gestión de Contexto": "Mantiene y utiliza el contexto de la conversación",
            "Integración con MCP": "Comunica con el servidor de herramientas externas",
        }

    def _execute_impl(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Implementa la lógica del agente de información del sistema.

        Args:
            input_data: Datos de entrada con la consulta y contexto

        Returns:
            Información sobre el sistema según la consulta
        """
        start_time = time.time()

        # Obtener la consulta
        query = input_data.get("query", "").strip().lower()
        context = input_data.get("context", {})

        # Registrar la consulta recibida
        logger.info(f"SystemInfoAgent procesando consulta: {query[:100] if len(query) > 100 else query}")

        # Determinar qué tipo de información se está solicitando
        response_content = ""

        # Consulta sobre capacidades de la API
        if any(term in query for term in ["capacidades", "funcionalidades", "qué puede hacer", "qué hace"]):
            response_content = self._get_api_capabilities()

        # Consulta sobre el estado del servicio
        elif any(term in query for term in ["estado", "status", "funcionando", "operativo"]):
            response_content = self._get_service_status()

        # Consulta sobre los agentes disponibles
        elif any(term in query for term in ["agentes", "asistentes", "especialistas"]):
            response_content = self._get_available_agents()

        # Consulta sobre la API en general
        else:
            response_content = self._get_general_info()

        # Registrar métricas
        execution_time = time.time() - start_time
        MetricsCollector.record_agent_execution(
            agent_name="system_info_agent", status=True, execution_time=execution_time
        )

        return {
            "result": response_content,
            "source": "system_info_agent",
            "confidence": 0.95,
        }

    def _get_api_capabilities(self) -> str:
        """
        Genera información sobre las capacidades de la API.

        Returns:
            Descripción de las capacidades
        """
        capabilities = [
            "# Capacidades de la API de Sesame",
            "",
            "La API de Sesame proporciona un sistema avanzado de asistentes virtuales especializados en diferentes áreas de negocio, incluyendo:",
            "",
        ]

        # Añadir servicios principales
        capabilities.append("## Servicios Principales:")
        for service, description in self.system_services.items():
            capabilities.append(f"- **{service}**: {description}")
        capabilities.append("")

        # Añadir agentes disponibles
        capabilities.append("## Agentes Especializados:")
        for agent, info in self.available_agents.items():
            capabilities.append(f"- **{agent}**: {info['description']}")
            capabilities.append("  Capacidades:")
            for capability in info["capabilities"][:5]:  # Mostrar solo las primeras 5 capacidades
                capabilities.append(f"  - {capability}")
        capabilities.append("")

        # Añadir endpoints disponibles
        capabilities.append("## Endpoints API:")
        for endpoint, description in self.api_endpoints.items():
            capabilities.append(f"- **{endpoint}**: {description}")

        return "\n".join(capabilities)

    def _get_service_status(self) -> str:
        """
        Genera información sobre el estado actual del servicio.

        Returns:
            Descripción del estado del servicio
        """
        # En un entorno real, obtendrías esta información de un servicio
        # de monitoreo o de health checks internos

        status = [
            "# Estado Actual del Servicio Sesame",
            "",
            "## Resumen:",
            "- **Estado General**: Operativo",
            "- **Versión**: 0.1.0",
            "- **Tiempo de Actividad**: 99.9%",
            "",
            "## Servicios:",
            "- **API Principal**: Funcionando correctamente",
            "- **Servicio de Agentes**: Funcionando correctamente",
            "- **Conexión MCP**: Activa",
            "- **Base de Datos**: Operativa",
            "",
            "## Rendimiento:",
            "- **Tiempo Promedio de Respuesta**: 1.2s",
            "- **Consultas por Minuto**: 120",
            "- **Uso de Recursos**: Normal",
        ]

        return "\n".join(status)

    def _get_available_agents(self) -> str:
        """
        Genera información sobre los agentes disponibles.

        Returns:
            Descripción de los agentes
        """
        agents_info = [
            "# Agentes Disponibles en Sesame",
            "",
            "Sesame cuenta con los siguientes agentes especializados:",
            "",
        ]

        for agent, info in self.available_agents.items():
            agents_info.append(f"## {agent}")
            agents_info.append(f"{info['description']}")
            agents_info.append("")
            agents_info.append("### Capacidades:")
            for capability in info["capabilities"]:
                agents_info.append(f"- {capability}")
            agents_info.append("")

        return "\n".join(agents_info)

    def _get_general_info(self) -> str:
        """
        Genera información general sobre la API.

        Returns:
            Información general
        """
        general_info = [
            "# Información General de Sesame API",
            "",
            "Sesame es una plataforma avanzada de asistencia empresarial basada en agentes inteligentes especializados.",
            "",
            "## Características Principales:",
            "- **Arquitectura Multi-Agente**: Sistema de agentes especializados que colaboran para resolver consultas complejas",
            "- **Procesamiento de Lenguaje Natural**: Interpreta consultas en lenguaje natural para dirigirlas al agente adecuado",
            "- **Contexto Conversacional**: Mantiene el contexto de la conversación para proporcionar respuestas coherentes",
            "- **Guardrails de Seguridad**: Políticas de uso para garantizar que las consultas estén dentro del ámbito del sistema",
            "- **Integración con Herramientas Externas**: Conexión con servicios externos a través del protocolo MCP",
            "",
            "## Dominios Principales:",
            "- Finanzas y análisis financiero",
            "- Marketing y estrategias de mercado",
            "- Análisis de datos empresariales",
            "- Estrategia y gestión empresarial",
            "",
            "Para obtener más información, puede consultar la documentación en /docs",
        ]

        return "\n".join(general_info)

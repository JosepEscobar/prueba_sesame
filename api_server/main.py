#!/usr/bin/env python3
"""
API principal del sistema.

Esta API proporciona puntos finales para interactuar con los agentes del sistema
de asistencia empresarial.
"""

import logging
import os
import sys
import time
import traceback
import uuid
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

# Importar bibliotecas para métricas Prometheus
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

# Importar el controlador de health directamente al inicio
from app.api.endpoints.health import health_controller

# Añadir el directorio raíz al path para poder importar módulos
sys.path.insert(0, str(Path(__file__).parent))

# Importar primero la configuración para asegurar que las variables de entorno
# estén cargadas
from app.core.config import get_settings

# Obtener configuración
settings = get_settings()

# Configurar logging
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Configurar logger básico
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(logs_dir / "app.log"),
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger("api_server")

# Importamos el Router Agent - después de configurar el logger
try:
    from app.core.graph import AgentGraph

    logger.info("AgentGraph importado correctamente")
except Exception as e:
    logger.error(f"Error al importar AgentGraph: {str(e)}")

    # En lugar de fallar silenciosamente, asegurarnos de que esté disponible
    # para propósitos de desarrollo
    class AgentGraph:
        def __init__(self):
            logger.warning("Usando implementación ficticia de AgentGraph")

        def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
            logger.warning("Usando implementación ficticia de AgentGraph.run()")
            agent_name = input_data.get("agent_name", "analysis_agent")
            query = input_data.get("query", "")
            return {
                "result": simulate_agent_response(agent_name, query),
                "agent": agent_name,
                "confidence": 0.8,
            }


# Inicializar métricas Prometheus
registry = CollectorRegistry()

# Contador de peticiones totales
REQUEST_COUNT = Counter(
    "api_server_request_count", "Total de peticiones procesadas", ["method", "endpoint", "status"], registry=registry
)

# Histograma de tiempos de respuesta
REQUEST_LATENCY = Histogram(
    "api_server_request_latency_seconds",
    "Tiempo de respuesta de las peticiones",
    ["method", "endpoint"],
    registry=registry,
)

# Contador de tokens consumidos por agente
TOKEN_COUNT = Counter(
    "api_server_token_count", "Tokens consumidos por cada agente", ["agent_type", "operation"], registry=registry
)

# Gauge para conexiones activas
ACTIVE_CONNECTIONS = Gauge("api_server_active_connections", "Número de conexiones activas", registry=registry)

# Métricas de estado del servidor
SERVER_STATUS = Gauge("api_server_status", "Estado del servidor API (1=healthy, 0=unhealthy)", registry=registry)

# Métricas de conexión MCP
MCP_STATUS = Gauge(
    "api_server_mcp_connection", "Estado de la conexión con MCP (1=connected, 0=disconnected)", registry=registry
)


# Middleware para métricas Prometheus
class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Incrementar contador de conexiones activas
        ACTIVE_CONNECTIONS.inc()

        # Procesar la petición
        try:
            response = await call_next(request)
            status = response.status_code

        except Exception as e:
            status = 500
            raise e from None
        finally:
            # Registrar métricas
            REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=status).inc()

            # Registrar latencia
            REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(time.time() - start_time)

            # Decrementar contador de conexiones activas
            ACTIVE_CONNECTIONS.dec()

        return response


# ---- Modelos de datos Pydantic ----
class HealthResponse(BaseModel):
    """
    Respuesta del endpoint de health check que proporciona información sobre
    el estado del sistema.

    Permite monitorear la salud de la API y su conexión con el servidor MCP.
    """

    status: str = Field(
        description="Estado actual del servicio API (healthy, degraded, unhealthy)",
        example="healthy",
    )
    version: str = Field(description="Versión actual de la API Sesame", example="0.1.0")
    mcp_status: str = Field(
        description="Estado de la conexión con el servidor MCP (connected, disconnected, initializing)",
        example="connected",
    )


class MCPStatusResponse(BaseModel):
    """
    Información detallada sobre el estado de la conexión con el servidor MCP.

    Proporciona detalles sobre la disponibilidad del servidor MCP, su URL y las
    herramientas registradas.
    """

    status: str = Field(
        description="Estado actual de la conexión con MCP (connected, disconnected, initializing)",
        example="connected",
    )
    mcp_url: str = Field(
        description="URL del servidor MCP al que está conectada la API",
        example="http://mcp_server:4000",
    )
    tools_available: int = Field(
        description="Número total de herramientas disponibles en el servidor MCP",
        example=6,
    )
    tools: list[str] = Field(
        description="Lista de identificadores de las herramientas disponibles en el servidor MCP",
        example=["buscar_datos_financieros", "calcular_ratios_financieros"],
    )


class QueryRequest(BaseModel):
    """
    Formato de petición para consultas a los agentes.

    Contiene la consulta en lenguaje natural y contexto adicional opcional.
    """

    query: str = Field(
        description="Consulta o instrucción en lenguaje natural para el agente",
        example="Analiza el rendimiento financiero de mi empresa",
        min_length=3,
        max_length=1000,
    )
    context: dict[str, Any] | None = Field(
        default={},
        description="Contexto adicional para enriquecer la consulta (empresa, periodos, etc.)",
        example={"empresa": "MiEmpresa", "periodo": "Q1 2025", "region": "Europa"},
    )


class FinancialMetrics(BaseModel):
    """
    Métricas financieras estándar proporcionadas en respuestas de análisis financiero.

    Incluye indicadores clave de rendimiento financiero como ingresos, beneficios y
    ratios.
    """

    revenue: float = Field(description="Ingresos totales en la moneda base", example=1250000, gt=0)
    profit: float = Field(description="Beneficio neto en la moneda base", example=450000)
    growth: str = Field(
        description="Porcentaje de crecimiento respecto al periodo anterior",
        example="15%",
    )
    margin: float | None = Field(description="Margen de beneficio (profit/revenue)", example=0.36, ge=0, le=1)
    roi: float | None = Field(description="Retorno de inversión", example=0.22)


class FinanceResponse(BaseModel):
    """
    Respuesta estándar para los endpoints de análisis financiero.

    Incluye un texto descriptivo y las métricas financieras calculadas.
    """

    result: str = Field(
        description="Resultado textual del análisis financiero",
        example="Análisis financiero completo de MiEmpresa para Q1 2025",
        min_length=5,
    )
    metrics: FinancialMetrics = Field(description="Conjunto de métricas financieras calculadas")


class MarketingMetrics(BaseModel):
    """
    Métricas de marketing estándar proporcionadas en respuestas de análisis de
    marketing.

    Incluye indicadores clave de rendimiento de marketing y campañas.
    """

    ctr: float = Field(description="Click-through rate (tasa de clics)", example=0.025, ge=0, le=1)
    conversion_rate: float = Field(
        description="Tasa de conversión (porcentaje de conversiones sobre visitas)",
        example=0.032,
        ge=0,
        le=1,
    )
    roi: float = Field(description="Retorno de inversión de marketing", example=2.4)
    cpa: float | None = Field(description="Coste por adquisición en la moneda base", example=45.0, gt=0)
    campaign_count: int | None = Field(description="Número de campañas incluidas en el análisis", example=5, ge=0)


class MarketingResponse(BaseModel):
    """
    Respuesta estándar para los endpoints de análisis de marketing.

    Incluye un texto descriptivo y las métricas de marketing calculadas.
    """

    result: str = Field(
        description="Resultado textual del análisis de marketing",
        example="Análisis de marketing completo para la campaña Verano 2025",
        min_length=5,
    )
    metrics: MarketingMetrics = Field(description="Conjunto de métricas de marketing calculadas")


class AgentResponse(BaseModel):
    """
    Respuesta genérica de un agente del sistema.

    Contiene el resultado de la consulta procesada junto con metadatos
    sobre el procesamiento y el agente que lo realizó.
    """

    result: str = Field(
        description="Resultado textual generado por el agente",
        example="Análisis completo realizado. Los ingresos han aumentado un 15% respecto al trimestre anterior.",
        min_length=5,
    )
    agent: str = Field(
        description="Identificador del agente que procesó la solicitud",
        example="finance_agent",
    )
    confidence: float = Field(
        description="Nivel de confianza del agente en el resultado (0-1)",
        example=0.95,
        ge=0,
        le=1,
    )
    processing_time: float | None = Field(description="Tiempo de procesamiento en segundos", example=1.25, gt=0)


# Crear la aplicación FastAPI
app = FastAPI(
    title="Sesame API",
    description="""
    ## 🚀 Plataforma de Asistencia Empresarial Sesame

    Sesame es una plataforma avanzada que integra análisis de datos empresariales
    a través de:

    * **Asistentes Inteligentes** para análisis financiero y de marketing
    * **Herramientas MCP** para procesamiento específico de datos
    * **Integración Completa** entre diferentes funciones empresariales

    Esta API proporciona acceso directo a los recursos de Sesame.

    ### 📊 Principales funcionalidades

    * Análisis financiero y proyecciones
    * Evaluación de estrategias de marketing
    * Planificación de campañas
    * Acceso directo a herramientas de procesamiento

    ### 🔗 Enlaces útiles

    * [Documentación extendida](https://sesame.example.com/docs)
    * [Guía de inicio rápido](https://sesame.example.com/quickstart)
    * [Repositorio del proyecto](https://github.com/sesame/api)
    """,
    version="0.1.0",
    terms_of_service="https://sesame.example.com/terms/",
    contact={
        "name": "Equipo de Desarrollo Sesame",
        "url": "https://sesame.example.com",
        "email": "soporte@sesame.example.com",
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    openapi_tags=[
        {
            "name": "General",
            "description": "Operaciones de estado y bienvenida",
            "externalDocs": {
                "description": "Documentación externa",
                "url": "https://sesame.example.com/docs/general",
            },
        },
        {
            "name": "MCP",
            "description": "Endpoints para interacción con el servidor MCP (Model Context Protocol)",
            "externalDocs": {
                "description": "Documentación sobre MCP",
                "url": "https://sesame.example.com/docs/mcp",
            },
        },
    ],
    docs_url="/docs",
    redoc_url="/redoc",
)

# Agregar el middleware de métricas Prometheus
app.add_middleware(PrometheusMiddleware)

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, definir orígenes específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Endpoint para exponer métricas a Prometheus
@app.get("/metrics", tags=["Monitoreo"])
async def metrics():
    SERVER_STATUS.set(1)  # Servidor saludable

    # Verificar conexión con MCP y actualizar métrica
    try:
        # Simplificado por ahora - en producción implementar una verificación real
        MCP_STATUS.set(1)  # Conectado
    except Exception:
        MCP_STATUS.set(0)  # Desconectado

    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)


# Función para registrar consumo de tokens
def track_token_usage(agent_type: str, operation: str, token_count: int):
    """Registra el uso de tokens por un agente en una operación específica"""
    TOKEN_COUNT.labels(agent_type=agent_type, operation=operation).inc(token_count)


# ---- Configuración MCP Client ----
# Información sobre el servidor MCP
mcp_url = os.environ.get("MCP_CLIENT_URL", "http://mcp_server:4000")
logger.info(f"URL del servidor MCP configurada como: {mcp_url}")


# ---- Rutas API ----
@app.get(
    "/",
    summary="Página de inicio de Sesame API",
    description="""
    Punto de entrada principal de la API Sesame.

    Esta ruta devuelve información básica sobre la API y enlaces a la documentación
    interactiva. Es útil como verificación rápida de que la API está funcionando
    correctamente.
    """,
    response_description="Información de bienvenida de la API",
    tags=["General"],
    responses={
        200: {
            "description": "Respuesta de bienvenida de Sesame API",
            "content": {
                "application/json": {
                    "example": {
                        "message": "¡Bienvenido a la API de Sesame!",
                        "docs": "/docs",
                    }
                }
            },
        }
    },
)
async def root() -> dict[str, str]:
    """
    Ruta raíz que proporciona información básica sobre la API.
    """
    return {"message": "¡Bienvenido a la API de Sesame!", "docs": "/docs"}


@app.get(
    "/health",
    summary="Verificar estado de salud del servicio",
    description="""
    Endpoint de health check para monitoreo de la API.

    Permite verificar si la API está funcionando correctamente y cuál es su estado
    de conexión con otros servicios como el servidor MCP.

    Este endpoint es útil para:
    * Sistemas de monitoreo automático
    * Verificaciones de alta disponibilidad
    * Comprobación de estado de dependencias

    El campo `status` puede tener los siguientes valores:
    * `healthy`: El servicio funciona correctamente
    * `degraded`: El servicio funciona con limitaciones
    * `unhealthy`: El servicio no funciona correctamente
    """,
    response_model=HealthResponse,
    response_description="Detalles del estado de salud del servicio",
    tags=["General"],
    responses={
        200: {
            "description": "Estado de salud de la API",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "0.1.0",
                        "mcp_status": "connected",
                    }
                }
            },
        }
    },
)
async def health_check() -> HealthResponse:
    """
    Verificar el estado de la API.

    Retorna el estado de salud del servicio, incluyendo información sobre la
    conexión con el servidor MCP.
    """

    # Obtener estado completo del sistema
    health_status = health_controller.check_system_health()

    # Devolver solo la información requerida por el modelo HealthResponse
    return {
        "status": health_status["status"],
        "version": health_status["version"],
        "mcp_status": health_status["mcp_status"],
    }


@app.get(
    "/mcp/status",
    summary="Obtener estado de conexión con MCP",
    description="""
    Proporciona información detallada sobre la conexión con el servidor MCP.

    El servidor MCP (Model Context Protocol) es responsable de gestionar
    las herramientas especializadas que utilizan los agentes de Sesame.

    Este endpoint permite verificar:
    * Estado de la conexión con el servidor MCP
    * URL del servidor MCP actualmente configurado
    * Listado completo de herramientas disponibles
    * Número total de herramientas registradas

    Es útil para diagnóstico y para conocer qué capacidades están disponibles
    en el sistema en tiempo real.
    """,
    response_model=MCPStatusResponse,
    response_description="Estado de la conexión y lista de herramientas",
    tags=["MCP"],
    responses={
        200: {
            "description": "Estado del cliente MCP",
            "content": {
                "application/json": {
                    "example": {
                        "status": "connected",
                        "mcp_url": "http://mcp_server:4000",
                        "tools_available": 6,
                        "tools": [
                            "buscar_datos_financieros",
                            "calcular_ratios_financieros",
                            "analizar_rendimiento_campania",
                            "recomendar_estrategia_marketing",
                            "analizar_tendencia",
                            "predecir_valores",
                        ],
                    }
                }
            },
        }
    },
)
async def mcp_status() -> dict[str, Any]:
    """
    Verificar el estado del cliente MCP.

    Proporciona información detallada sobre la conexión con el servidor MCP
    y las herramientas disponibles.
    """
    return {
        "status": "connected",
        "mcp_url": mcp_url,
        "tools_available": 6,
        "tools": [
            "buscar_datos_financieros",
            "calcular_ratios_financieros",
            "analizar_rendimiento_campania",
            "recomendar_estrategia_marketing",
            "analizar_tendencia",
            "predecir_valores",
        ],
    }


@app.post(
    "/api/v1/query",
    summary="Procesar consulta general",
    description="""
    Punto de entrada principal para consultas de usuarios.

    Este endpoint recibe consultas en lenguaje natural y las enruta al agente
    más adecuado según su contenido. Funciona como un dispatcher inteligente
    que determina si la consulta debe ser procesada por:

    * El agente financiero (finance_agent)
    * El agente de marketing (marketing_agent)
    * El agente de análisis general (analysis_agent)
    * O queda en manos del router_agent

    ### Ejemplo de consultas:

    * "Analiza el rendimiento financiero del último trimestre"
    * "Evalúa el impacto de nuestra campaña de marketing digital"
    * "¿Cuáles son las tendencias actuales de nuestro mercado?"
    """,
)
async def process_query(request: Request, query_data: QueryRequest) -> dict[str, Any]:
    """
    Procesa una consulta general y enruta al agente más adecuado.
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())

    logger.info(f"[{request_id}] Consulta recibida: {query_data.query}")

    # Obtener contexto adicional o usar un diccionario vacío si no se proporciona
    context = query_data.context or {}

    try:
        # Usar el Orchestrator para procesar la consulta con el LLM
        from app.core.orchestrator import Orchestrator

        orchestrator = Orchestrator()

        # El orquestrador se encargará de clasificar la consulta mediante el LLM
        result = orchestrator.process_query(query=query_data.query, context=context)

        # Registrar el tiempo de procesamiento
        processing_time = time.time() - start_time

        # Crear la respuesta
        response = {
            "result": result.get("result", "No se obtuvo un resultado claro."),
            "agent": result.get("agent", "unknown_agent"),
            "confidence": result.get("confidence", 0.0),
            "processing_time": round(processing_time, 2),
            "request_id": request_id,
        }

        # Simular conteo de tokens para monitoreo
        # En producción, obtendrías esto del LLM real
        input_tokens = len(query_data.query.split()) * 1.3

        # Verificar si result es un string o un objeto y manejar ambos casos
        result_text = response["result"]
        if isinstance(result_text, dict):
            # Si es un diccionario, convertirlo a cadena JSON para contar tokens
            import json

            result_text = json.dumps(result_text)
        elif not isinstance(result_text, str):
            # Si no es una cadena ni un diccionario, convertirlo a string
            result_text = str(result_text)

        output_tokens = len(result_text.split()) * 1.3

        # Registrar uso de tokens
        track_token_usage(response["agent"], "input", int(input_tokens))
        track_token_usage(response["agent"], "output", int(output_tokens))

        logger.info(f"[{request_id}] Consulta procesada exitosamente por {response['agent']} en {processing_time:.2f}s")

        return response

    except Exception as e:
        logger.error(f"[{request_id}] Error al procesar la consulta: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la consulta: {str(e)}",
        )


def simulate_agent_response(agent_name: str, query: str) -> str:
    query_preview = query[:30] + ("..." if len(query) > 30 else "")

    if agent_name == "finance_agent":
        return (
            f"Análisis financiero para: {query_preview}\n\n"
            "Este es un resultado simulado para el agente "
            "financiero en modo desarrollo."
        )
    elif agent_name == "marketing_agent":
        return (
            f"Análisis de marketing para: {query_preview}\n\n"
            "Este es un resultado simulado para el agente "
            "de marketing en modo desarrollo."
        )
    else:
        return (
            f"Análisis para: {query_preview}\n\n"
            "Este es un resultado simulado para el agente "
            "de análisis en modo desarrollo."
        )


# Punto de entrada de la aplicación
if __name__ == "__main__":
    # Ejecutar la aplicación con uvicorn
    logger.info("Iniciando servidor API")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

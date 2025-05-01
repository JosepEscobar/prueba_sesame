import asyncio
import time
import traceback
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, RedirectResponse
from prometheus_client import make_asgi_app
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.router import api_router
from app.api.routes import router as routes_router
from app.core.config import get_settings
from app.core.logging import logger, setup_logging
from app.core.metrics import setup_metrics
from app.tools.mcp_adapter import get_mcp_tools
from app.tools.register_tools import register_all_tools
from app.tools.server.server_init import (
    start_mcp_server_process,
    stop_mcp_server_process,
)

# Configuración de logging
setup_logging()

# Rutas
api_router = api_router

# Configuración
settings = get_settings()

# Captura de errores con Sentry (si está configurado)
if settings.SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.2,
        environment=settings.ENVIRONMENT,
    )
    logger.info("Sentry inicializado para captura de errores")

# Variable global para el proceso del servidor MCP
mcp_process = None


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware para agregar un timeout a todas las solicitudes."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            # Establecer un timeout de 10 segundos para todas las solicitudes
            return await asyncio.wait_for(call_next(request), timeout=10.0)
        except TimeoutError:
            logger.error(
                f"Timeout en la solicitud: {request.method} {request.url.path}"
            )
            return JSONResponse(
                status_code=504,
                content={
                    "detail": "La solicitud excedió el tiempo límite de 10 segundos"
                },
            )
        except Exception as e:
            logger.error(f"Error inesperado en el middleware: {str(e)}")
            return JSONResponse(
                status_code=500, content={"detail": "Error interno del servidor"}
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para registrar solicitudes HTTP."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "unknown")

        logger.info(
            f"Solicitud iniciada: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            logger.info(
                f"Solicitud completada: {request.method} {request.url.path} - {response.status_code} en {process_time:.4f}s",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": process_time,
                },
            )

            # Añadir cabecera de tiempo de procesamiento
            response.headers["X-Process-Time"] = str(process_time)
            return response

        except Exception as e:
            process_time = time.time() - start_time
            error_traceback = traceback.format_exc()

            logger.error(
                f"Error en solicitud: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "process_time": process_time,
                    "exc_info": error_traceback,
                },
            )

            # En caso de error no controlado, devolver respuesta de error 500
            return JSONResponse(
                status_code=500, content={"detail": "Error interno del servidor"}
            )


class ResponseLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para registrar todas las respuestas HTTP con su contenido."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "unknown")

        path = request.url.path
        method = request.method

        # Solo loguear ciertas rutas, especialmente las APIs
        if "/api/" in path:
            try:
                body = await request.body()
                if body:
                    try:
                        # Intentar capturar el cuerpo JSON
                        body_str = body.decode("utf-8")
                        logger.info(
                            f"Cuerpo de la solicitud: {body_str}",
                            extra={
                                "request_id": request_id,
                                "path": path,
                                "method": method,
                            },
                        )
                    except Exception as e:
                        logger.warning(f"No se pudo decodificar el cuerpo: {str(e)}")
            except Exception as e:
                logger.warning(f"No se pudo leer el cuerpo de la solicitud: {str(e)}")

        # Procesar la solicitud
        response = await call_next(request)

        # Si es una respuesta JSON de la API, capturar y loguear el contenido completo
        if "/api/" in path and "application/json" in response.headers.get(
            "content-type", ""
        ):
            try:
                # Necesitamos leer el cuerpo de la respuesta
                original_body = b""
                async for chunk in response.body_iterator:
                    original_body += chunk

                # Decodificar para loguear
                body_str = original_body.decode("utf-8")

                # Loguear el cuerpo completo para depuración
                process_time = time.time() - start_time
                logger.info(
                    f"Respuesta completa: {body_str} (tiempo: {process_time:.4f}s)",
                    extra={
                        "request_id": request_id,
                        "path": path,
                        "method": method,
                        "status_code": response.status_code,
                        "process_time": process_time,
                    },
                )

                # Crear una nueva respuesta con el mismo cuerpo
                return Response(
                    content=original_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
            except Exception as e:
                logger.error(f"Error al loguear respuesta: {str(e)}")
                return response

        # Registrar tiempo para todas las respuestas
        process_time = time.time() - start_time
        logger.debug(
            f"Respuesta procesada: {method} {path} - {response.status_code} en {process_time:.4f}s",
            extra={
                "request_id": request_id,
                "path": path,
                "method": method,
                "status_code": response.status_code,
                "process_time": process_time,
            },
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Contexto de vida de la aplicación.
    Se ejecuta al iniciar y detener la aplicación.
    """
    global mcp_process

    try:
        # Iniciar el servidor MCP en un proceso separado
        logger.info("Iniciando servidor MCP en un proceso separado...")
        mcp_process = start_mcp_server_process(
            host=settings.MCP_HOST, port=settings.MCP_PORT
        )

        if mcp_process is None:
            logger.error(
                "No se pudo iniciar el servidor MCP. La aplicación continuará pero las herramientas MCP no estarán disponibles."
            )
        else:
            logger.info(f"Servidor MCP iniciado con PID {mcp_process.pid}")

            # Esperar más tiempo para asegurar que el servidor MCP esté completamente iniciado
            # y haya cargado todas las herramientas
            logger.info(
                "Esperando a que el servidor MCP esté completamente iniciado..."
            )
            time.sleep(5)

            # Verificar que el proceso sigue en ejecución
            if mcp_process.poll() is not None:
                exit_code = mcp_process.poll()
                logger.error(
                    f"El proceso del servidor MCP se detuvo con código de salida {exit_code}"
                )
                # Intentar leer los logs de error
                stdout, stderr = mcp_process.communicate()
                if stderr:
                    logger.error(f"Error del servidor MCP: {stderr}")
                mcp_process = None
            else:
                logger.info("Servidor MCP en ejecución correctamente")
    except Exception as e:
        logger.error(f"Error al iniciar el servidor MCP: {str(e)}")
        logger.warning(
            "La aplicación continuará pero las herramientas MCP no estarán disponibles."
        )

    # Continuar con la inicialización de la aplicación
    logger.info("Iniciando aplicación FastAPI...")

    # Registrar herramientas disponibles para los agentes
    tool_stats = register_all_tools()
    logger.info(
        f"Herramientas registradas: {tool_stats['implemented_tools']}/{tool_stats['total_tools']}"
    )

    # Cargar herramientas MCP adaptadas
    tools = get_mcp_tools()
    logger.info(
        f"Herramientas MCP adaptadas cargadas: {len(tools)} herramientas disponibles"
    )

    yield

    # Código que se ejecuta al detener la aplicación
    logger.info("Deteniendo la aplicación...")

    # Detener el servidor MCP si está en ejecución
    if mcp_process is not None:
        logger.info("Deteniendo servidor MCP...")
        success = stop_mcp_server_process()
        if success:
            logger.info("Servidor MCP detenido correctamente")
        else:
            logger.error("Error al detener el servidor MCP")


# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="API para el sistema multi-agente",
    version="0.1.0",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    lifespan=lifespan,
)

# Configuración de métricas
setup_metrics(app)

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta para métricas Prometheus
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Middleware para logging de solicitudes
app.add_middleware(RequestLoggingMiddleware)

# Middleware para logging de respuestas
app.add_middleware(ResponseLoggingMiddleware)

# Middleware para timeout
app.add_middleware(TimeoutMiddleware)

# Incluir rutas
app.include_router(api_router, prefix=settings.API_PREFIX)
app.include_router(routes_router, prefix=settings.API_PREFIX)


# Endpoint raíz
@app.get(
    "/",
    tags=["system"],
    summary="Punto de entrada principal",
    description="Devuelve un mensaje de bienvenida con información básica sobre el sistema",
)
async def root() -> dict:
    """
    Endpoint raíz que muestra información básica de la API.

    Proporciona detalles sobre:
    - Nombre del sistema
    - Estado actual
    - Entorno de ejecución
    - Versión de la API
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": "0.1.0",
        "docs": f"{settings.API_PREFIX}/docs",
    }


# Endpoint de chequeo de salud
@app.get(
    "/health",
    tags=["system"],
    summary="Verificar estado del sistema",
    description="Devuelve información sobre el estado de salud del sistema y sus componentes",
)
async def health_check() -> dict:
    """
    Endpoint para verificar el estado de la aplicación y sus servicios.
    """
    health_status = {
        "status": "ok",
        "version": settings.VERSION,
        "services": {
            "api": "ok",
        },
    }

    # Verificar estado del servidor MCP
    if mcp_process is not None:
        # Si el proceso ha terminado (poll() devuelve código de salida)
        if mcp_process.poll() is not None:
            exit_code = mcp_process.poll()
            health_status["services"]["mcp_server"] = (
                f"error: proceso terminado con código {exit_code}"
            )
        else:
            health_status["services"]["mcp_server"] = "ok"
    else:
        health_status["services"]["mcp_server"] = "no iniciado"

    return health_status


# Personalizar el esquema OpenAPI para añadir más metadatos
def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Añadir ejemplos adicionales, esquemas o metadatos según sea necesario
    openapi_schema["info"]["x-logo"] = {"url": "https://multiagentsystem.com/logo.png"}

    # Añadir servidores de producción y desarrollo para pruebas
    openapi_schema["servers"] = [
        {
            "url": "https://api.multiagentsystem.com",
            "description": "Servidor de producción",
        },
        {
            "url": "https://staging-api.multiagentsystem.com",
            "description": "Servidor de staging",
        },
        {"url": "http://localhost:8000", "description": "Servidor local de desarrollo"},
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Crear una aplicación para redirigir /docs a /api/v1/docs
@app.get("/docs", include_in_schema=False)
def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse(url="/api/v1/docs")


# Opcional: Exponer endpoint para listarlas
@app.get(f"{settings.API_PREFIX}/mcp-tools")
async def list_mcp_tools() -> list[dict[str, str]]:
    """Devuelve la lista de herramientas MCP adaptadas a LangChain."""
    # Obtenemos las herramientas cada vez que se llama al endpoint
    tools = get_mcp_tools()
    return [{"name": t.name, "description": t.description} for t in tools]


# Punto de entrada para ejecución directa
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG
    )

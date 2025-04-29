import time
import uuid
import contextlib
import asyncio
from fastapi import FastAPI, Request, Depends, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from prometheus_client import make_asgi_app
import logging
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.logging import setup_logging, logger
from app.core.metrics import setup_metrics
from app.api.router import api_router
from app.tools.register_tools import register_all_tools
from app.tools.server.server_init import start_mcp_server_process, stop_mcp_server_process
import uvicorn
import os
import sys
from pathlib import Path

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
            host=settings.MCP_HOST, 
            port=settings.MCP_PORT
        )
        
        if mcp_process is None:
            logger.error("No se pudo iniciar el servidor MCP. La aplicación continuará pero las herramientas MCP no estarán disponibles.")
        else:
            logger.info(f"Servidor MCP iniciado con PID {mcp_process.pid}")
            
            # Esperar más tiempo para asegurar que el servidor MCP esté completamente iniciado
            # y haya cargado todas las herramientas
            logger.info("Esperando a que el servidor MCP esté completamente iniciado...")
            time.sleep(5)
            
            # Verificar que el proceso sigue en ejecución
            if mcp_process.poll() is not None:
                exit_code = mcp_process.poll()
                logger.error(f"El proceso del servidor MCP se detuvo con código de salida {exit_code}")
                # Intentar leer los logs de error
                stdout, stderr = mcp_process.communicate()
                if stderr:
                    logger.error(f"Error del servidor MCP: {stderr}")
                mcp_process = None
            else:
                logger.info("Servidor MCP en ejecución correctamente")
    except Exception as e:
        logger.error(f"Error al iniciar el servidor MCP: {str(e)}")
        logger.warning("La aplicación continuará pero las herramientas MCP no estarán disponibles.")
    
    # Continuar con la inicialización de la aplicación
    logger.info("Iniciando aplicación FastAPI...")
    
    # Registrar herramientas disponibles para los agentes
    tool_stats = register_all_tools()
    logger.info(f"Herramientas registradas: {tool_stats['implemented_tools']}/{tool_stats['total_tools']}")
    
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
    lifespan=lifespan
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

# Middleware para logging de solicitudes HTTP
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Registra información sobre cada solicitud HTTP."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    logger.info(
        f"Solicitud iniciada: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None
        }
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"Solicitud completada: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time
            }
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        
        logger.error(
            f"Error en solicitud: {request.method} {request.url.path} - {str(e)}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "process_time": process_time
            },
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Error interno del servidor",
                "request_id": request_id
            }
        )

# Incluir rutas
app.include_router(api_router, prefix=settings.API_PREFIX)

# Endpoint raíz
@app.get("/", 
    tags=["system"],
    summary="Punto de entrada principal",
    description="Devuelve un mensaje de bienvenida con información básica sobre el sistema"
)
async def root():
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
        "docs": f"{settings.API_PREFIX}/docs"
    }

# Endpoint de chequeo de salud
@app.get("/health", 
    tags=["system"],
    summary="Verificar estado del sistema",
    description="Devuelve información sobre el estado de salud del sistema y sus componentes"
)
async def health_check():
    """
    Endpoint para verificar el estado de la aplicación y sus servicios.
    """
    health_status = {
        "status": "ok",
        "version": settings.VERSION,
        "services": {
            "api": "ok",
        }
    }
    
    # Verificar estado del servidor MCP
    if mcp_process is not None:
        # Si el proceso ha terminado (poll() devuelve código de salida)
        if mcp_process.poll() is not None:
            exit_code = mcp_process.poll()
            health_status["services"]["mcp_server"] = f"error: proceso terminado con código {exit_code}"
        else:
            health_status["services"]["mcp_server"] = "ok"
    else:
        health_status["services"]["mcp_server"] = "no iniciado"
    
    return health_status

# Personalizar el esquema OpenAPI para añadir más metadatos
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Añadir ejemplos adicionales, esquemas o metadatos según sea necesario
    openapi_schema["info"]["x-logo"] = {
        "url": "https://multiagentsystem.com/logo.png"
    }
    
    # Añadir servidores de producción y desarrollo para pruebas
    openapi_schema["servers"] = [
        {"url": "https://api.multiagentsystem.com", "description": "Servidor de producción"},
        {"url": "https://staging-api.multiagentsystem.com", "description": "Servidor de staging"},
        {"url": "http://localhost:8000", "description": "Servidor local de desarrollo"}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi 

# Crear una aplicación para redirigir /docs a /api/v1/docs
@app.get("/docs", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/api/v1/docs")

# Punto de entrada para ejecución directa
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 
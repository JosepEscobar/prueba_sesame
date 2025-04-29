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
from app.tools.server.server_init import init_mcp_server

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

# Variable para almacenar el servidor MCP
mcp_server = None

# Manejador de ciclo de vida de la aplicación
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código de inicialización (antes era startup_event)
    global mcp_server
    
    logger.info(f"Starting {settings.APP_NAME}...")
    
    # Iniciar el servidor MCP
    try:
        logger.info("Iniciando servidor MCP...")
        mcp_server = await init_mcp_server(
            host=settings.MCP_HOST if hasattr(settings, 'MCP_HOST') else "localhost",
            port=settings.MCP_PORT if hasattr(settings, 'MCP_PORT') else 4000
        )
        
        # Iniciar el servidor con un timeout y manejo mejorado de errores
        start_success = await asyncio.wait_for(
            mcp_server.start_server(),
            timeout=10.0  # 10 segundos de timeout
        )
        
        if start_success:
            logger.info("Servidor MCP iniciado correctamente")
        else:
            logger.error("No se pudo iniciar el servidor MCP")
            mcp_server = None
    except asyncio.TimeoutError:
        logger.error("Timeout al iniciar el servidor MCP")
        mcp_server = None
    except Exception as e:
        logger.error(f"Error al iniciar el servidor MCP: {str(e)}")
        mcp_server = None
    
    # Registrar herramientas disponibles para los agentes
    # Ahora esperamos un corto tiempo para que el servidor MCP inicie completamente
    await asyncio.sleep(1.0)  # Esperar 1 segundo
    tool_stats = register_all_tools()
    logger.info(f"Herramientas registradas: {tool_stats['implemented_tools']}/{tool_stats['total_tools']}")
    
    # Ceder el control a la aplicación
    yield
    
    # Código de finalización (antes era shutdown_event)
    logger.info(f"Shutting down {settings.APP_NAME}...")
    
    # Detener el servidor MCP si está en ejecución
    if mcp_server and mcp_server.is_running():
        logger.info("Deteniendo servidor MCP...")
        try:
            await asyncio.wait_for(
                mcp_server.stop_server(),
                timeout=5.0  # 5 segundos de timeout
            )
            logger.info("Servidor MCP detenido correctamente")
        except asyncio.TimeoutError:
            logger.error("Timeout al detener el servidor MCP")
        except Exception as e:
            logger.error(f"Error al detener el servidor MCP: {str(e)}")

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
    Endpoint para comprobar si el servicio está funcionando correctamente.
    
    Utilizado para:
    - Monitoreo de disponibilidad
    - Verificación de estado en balanceadores de carga
    - Comprobación de funcionamiento por parte de herramientas de supervisión
    
    Devuelve:
    - Estado actual del sistema ("ok" si funciona correctamente)
    - Marca de tiempo actual de la solicitud
    """
    # Verificar si el servidor MCP está en ejecución
    mcp_status = "running" if mcp_server and mcp_server.is_running() else "not_running"
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "mcp_server": mcp_status
        }
    }

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
import time
import uuid
import contextlib
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

# Configuración de logging
from app.core.logging import setup_logging, logger

# Configuración de métricas
from app.core.metrics import MetricsMiddleware

# Rutas
from app.api.router import api_router

# Configuración
from app.core.config import get_settings, Settings

# Inicializar logger
setup_logging()

# Captura de errores con Sentry (si está configurado)
settings = get_settings()
if settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.2,
        environment=settings.ENVIRONMENT,
    )
    logger.info("Sentry inicializado para captura de errores")

# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema Multi-Agente basado en LangGraph para procesar consultas de forma inteligente",
    version="0.1.0",
    debug=settings.DEBUG
)

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Middleware de métricas
app.add_middleware(MetricsMiddleware)

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
@app.get("/")
def root():
    """Endpoint raíz que muestra información básica de la API."""
    return {
        "name": settings.APP_NAME,
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "api_version": "v1"
    }

# Endpoint de chequeo de salud
@app.get("/health")
def health_check():
    """Endpoint para comprobar si el servicio está funcionando correctamente."""
    return {
        "status": "ok",
        "timestamp": time.time()
    } 
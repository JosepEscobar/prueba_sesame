from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk
import time
import uuid
from prometheus_client import make_asgi_app
from app.core.config import get_settings
from app.api.v1.router import api_router
from app.core.logging import logger
from app.core.metrics import MetricsMiddleware

settings = get_settings()

# Configuración de Sentry
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema Multi-Agente MCP con LangGraph y FastAPI",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Añadir middleware de métricas
app.add_middleware(MetricsMiddleware)

# Añadir endpoint para métricas de Prometheus
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Middleware para logging de solicitudes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Añadir request_id a los logs
    logger.info(
        f"Solicitud recibida: {request.method} {request.url.path}",
        extra={"request_id": request_id}
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"Solicitud completada: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "process_time": process_time,
                "status_code": response.status_code
            }
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        
        logger.error(
            f"Error en solicitud: {request.method} {request.url.path} - {str(e)}",
            extra={
                "request_id": request_id,
                "process_time": process_time,
                "error": str(e)
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"}
        )

# Incluir el router de la API
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    logger.info("Acceso a la ruta raíz")
    return {
        "message": "Bienvenido al Sistema Multi-Agente MCP",
        "version": "1.0.0",
        "status": "operational",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/health")
async def health_check():
    logger.info("Verificación de salud")
    return {
        "status": "healthy",
        "version": "1.0.0",
        "api_version": "v1"
    } 
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk
import time
import uuid
from prometheus_client import make_asgi_app
from app.core.config import get_settings
from app.api.v1.router import api_router
from app.core.logging import logger, setup_logging
from app.core.metrics import MetricsMiddleware
from app.core.orchestrator import Orchestrator
from app.api.models import QueryRequest, QueryResponse

settings = get_settings()

# Configurar logging
setup_logging()

# Configuración de Sentry
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.2
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

# Crear una instancia global del orquestador
orchestrator = Orchestrator()

# Middleware para logging de solicitudes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Agregar request_id a la solicitud para tracking
    request.state.request_id = request_id
    
    # Loguear la solicitud entrante
    logger.info(
        f"Solicitud entrante: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_host": request.client.host if request.client else "unknown"
        }
    )
    
    try:
        # Procesar la solicitud
        response = await call_next(request)
        
        # Calcular tiempo de procesamiento
        process_time = time.time() - start_time
        
        # Loguear la respuesta
        logger.info(
            f"Respuesta enviada: {response.status_code}",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": process_time
            }
        )
        
        # Agregar headers de tiempo de procesamiento y request_id
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        # Loguear el error
        logger.error(
            f"Error procesando solicitud: {str(e)}",
            extra={
                "request_id": request_id,
                "error": str(e),
                "path": request.url.path
            }
        )
        
        # Calcular tiempo hasta el error
        process_time = time.time() - start_time
        
        # Devolver error 500
        return JSONResponse(
            status_code=500,
            content={
                "error": "Error interno del servidor",
                "request_id": request_id
            }
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

# Endpoint para procesar consultas
@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, request_obj: Request):
    """
    Procesa una consulta utilizando el sistema multi-agente.
    
    La consulta se enruta automáticamente al agente especializado más apropiado.
    """
    # Extraer request_id del middleware
    request_id = getattr(request_obj.state, "request_id", str(uuid.uuid4()))
    
    # Convertir solicitud a diccionario y agregar request_id
    query_data = request.dict()
    query_data["request_id"] = request_id
    
    logger.info(
        f"Procesando consulta de usuario",
        extra={
            "request_id": request_id,
            "query": query_data.get("query", "")[:100]
        }
    )
    
    try:
        # Procesar la consulta a través del orquestador
        result = await orchestrator.process_request(query_data)
        
        # Si hay un error, lanzar excepción
        if not result.get("success", True):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Error al procesar la consulta")
            )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Error procesando consulta: {str(e)}",
            extra={
                "request_id": request_id,
                "error": str(e)
            }
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la consulta: {str(e)}"
        ) 
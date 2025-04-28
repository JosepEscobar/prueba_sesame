from prometheus_client import Counter, Histogram, Gauge
from typing import Dict, Any
import time
from app.core.logging import logger

# Métricas para agentes
AGENT_EXECUTION_TIME = Histogram(
    "agent_execution_seconds",
    "Tiempo de ejecución de los agentes",
    ["agent_name"]
)

AGENT_EXECUTION_COUNT = Counter(
    "agent_execution_total",
    "Número total de ejecuciones de agentes",
    ["agent_name", "status"]
)

AGENT_CONFIDENCE = Gauge(
    "agent_confidence",
    "Nivel de confianza del agente",
    ["agent_name"]
)

# Métricas para tokens
TOKEN_USAGE = Counter(
    "token_usage_total",
    "Uso total de tokens",
    ["agent_name", "model"]
)

# Métricas para errores
ERROR_COUNT = Counter(
    "error_total",
    "Número total de errores",
    ["agent_name", "error_type"]
)

class MetricsCollector:
    """Recolector de métricas para el sistema de agentes."""
    
    @staticmethod
    def record_agent_execution(agent_name: str, execution_time: float, status: str = "success") -> None:
        """Registra la ejecución de un agente."""
        AGENT_EXECUTION_TIME.labels(agent_name=agent_name).observe(execution_time)
        AGENT_EXECUTION_COUNT.labels(agent_name=agent_name, status=status).inc()
        
        logger.info(
            f"Agente {agent_name} ejecutado",
            extra={
                "agent_name": agent_name,
                "execution_time": execution_time,
                "status": status
            }
        )
    
    @staticmethod
    def record_agent_confidence(agent_name: str, confidence: float) -> None:
        """Registra el nivel de confianza de un agente."""
        AGENT_CONFIDENCE.labels(agent_name=agent_name).set(confidence)
        
        logger.info(
            f"Confianza del agente {agent_name}: {confidence}",
            extra={
                "agent_name": agent_name,
                "confidence": confidence
            }
        )
    
    @staticmethod
    def record_token_usage(agent_name: str, model: str, token_count: int) -> None:
        """Registra el uso de tokens."""
        TOKEN_USAGE.labels(agent_name=agent_name, model=model).inc(token_count)
        
        logger.info(
            f"Uso de tokens para {agent_name} con modelo {model}: {token_count}",
            extra={
                "agent_name": agent_name,
                "model": model,
                "token_count": token_count
            }
        )
    
    @staticmethod
    def record_error(agent_name: str, error_type: str) -> None:
        """Registra un error."""
        ERROR_COUNT.labels(agent_name=agent_name, error_type=error_type).inc()
        
        logger.error(
            f"Error en agente {agent_name}: {error_type}",
            extra={
                "agent_name": agent_name,
                "error_type": error_type
            }
        )

class MetricsMiddleware:
    """Middleware para recopilar métricas de las solicitudes HTTP."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        start_time = time.time()
        
        # Función para enviar la respuesta con métricas
        async def send_with_metrics(message):
            if message["type"] == "http.response.start":
                # Calcular tiempo de respuesta
                response_time = time.time() - start_time
                
                # Registrar métricas
                AGENT_EXECUTION_TIME.labels(agent_name="http").observe(response_time)
                AGENT_EXECUTION_COUNT.labels(agent_name="http", status="success").inc()
                
                logger.info(
                    "Solicitud HTTP procesada",
                    extra={
                        "path": scope["path"],
                        "method": scope["method"],
                        "response_time": response_time,
                        "status_code": message["status"]
                    }
                )
            
            await send(message)
        
        return await self.app(scope, receive, send_with_metrics) 
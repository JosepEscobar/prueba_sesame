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

# Métricas para herramientas
TOOL_EXECUTION_TIME = Histogram(
    "tool_execution_seconds",
    "Tiempo de ejecución de herramientas",
    ["tool_name"]
)

TOOL_CALLS_TOTAL = Counter(
    "tool_calls_total",
    "Número total de llamadas a herramientas",
    ["tool_name", "status"]
)

# Objeto metrics que se puede importar desde otros módulos
class Metrics:
    """Clase que proporciona acceso a las métricas para otros módulos."""
    
    def __init__(self):
        self.agent_execution_time = AGENT_EXECUTION_TIME
        self.agent_execution_count = AGENT_EXECUTION_COUNT
        self.agent_confidence = AGENT_CONFIDENCE
        self.token_usage = TOKEN_USAGE
        self.error_count = ERROR_COUNT
        self.tool_execution_time = TOOL_EXECUTION_TIME
        self.tool_calls_total = TOOL_CALLS_TOTAL

# Instancia única de metrics para importar
metrics = Metrics()

def setup_metrics(app=None):
    """Configura las métricas para la aplicación.
    
    Args:
        app: Instancia de la aplicación FastAPI.
    """
    logger.info("Configurando métricas de Prometheus")
    # Aquí puedes agregar configuración adicional de métricas
    # Por ejemplo, configurar métricas específicas para la aplicación
    return app

class MetricsCollector:
    """Recolector de métricas para el sistema de agentes."""
    
    @staticmethod
    def start_timer() -> float:
        """Inicia un temporizador y retorna el tiempo de inicio."""
        return time.time()
    
    @staticmethod
    def stop_timer(start_time: float) -> float:
        """Detiene un temporizador y retorna la duración."""
        return time.time() - start_time
    
    @staticmethod
    def record_agent_execution(agent_name: str, status: bool = True, execution_time: float = None) -> None:
        """Registra la ejecución de un agente."""
        status_str = "success" if status else "failure"
        if execution_time is None:
            execution_time = 0.0
            
        AGENT_EXECUTION_TIME.labels(agent_name=agent_name).observe(execution_time)
        AGENT_EXECUTION_COUNT.labels(agent_name=agent_name, status=status_str).inc()
        
        logger.info(
            f"Agente {agent_name} ejecutado",
            extra={
                "agent_name": agent_name,
                "execution_time": execution_time,
                "status": status_str
            }
        )
    
    @staticmethod
    def record_execution(service_name: str, operation: str, execution_time: float, status: str = "success") -> None:
        """Registra la ejecución de una operación de servicio."""
        operation_name = f"{service_name}_{operation}"
        AGENT_EXECUTION_TIME.labels(agent_name=operation_name).observe(execution_time)
        AGENT_EXECUTION_COUNT.labels(agent_name=operation_name, status=status).inc()
        
        logger.info(
            f"Operación {operation} en servicio {service_name} ejecutada",
            extra={
                "service_name": service_name,
                "operation": operation,
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
        
    @staticmethod
    def record_data_lookup(lookup_type: str, success: bool, execution_time: float) -> None:
        """Registra una búsqueda de datos."""
        status_str = "success" if success else "failure"
        agent_name = f"data_lookup_{lookup_type}"
        
        AGENT_EXECUTION_TIME.labels(agent_name=agent_name).observe(execution_time)
        AGENT_EXECUTION_COUNT.labels(agent_name=agent_name, status=status_str).inc()
        
        logger.info(
            f"Búsqueda de datos {lookup_type} realizada",
            extra={
                "lookup_type": lookup_type,
                "execution_time": execution_time,
                "status": status_str
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
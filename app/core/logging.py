import logging
import json
import sys
from typing import Any, Dict
from pythonjsonlogger import jsonlogger
from app.core.config import get_settings

settings = get_settings()

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Formateador personalizado para logs en formato JSON."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Añade campos adicionales al registro de log."""
        super().add_fields(log_record, record, message_dict)
        
        # Añadir campos estándar
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        
        # Añadir campos específicos de la aplicación
        log_record["app_name"] = settings.APP_NAME
        log_record["environment"] = "development" if settings.DEBUG else "production"
        
        # Añadir información de la solicitud si está disponible
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
            
        if hasattr(record, "agent_name"):
            log_record["agent_name"] = record.agent_name
            
        if hasattr(record, "confidence"):
            log_record["confidence"] = record.confidence

def setup_logging() -> None:
    """Configura el sistema de logging."""
    # Crear el logger principal
    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Eliminar handlers existentes
    logger.handlers = []
    
    # Crear handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Configurar el formateador
    if settings.LOG_FORMAT == "json":
        formatter = CustomJsonFormatter(
            "%(asctime)s %(level)s %(name)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Configurar loggers de terceros
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    return logger

# Crear el logger principal
logger = setup_logging() 
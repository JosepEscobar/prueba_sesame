import logging
import json
import sys
import os
from typing import Any, Dict
from logging.handlers import RotatingFileHandler
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
    
    # Configurar el formateador
    if settings.LOG_FORMAT == "json":
        formatter = CustomJsonFormatter(
            "%(asctime)s %(level)s %(name)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Crear directorio de logs si no existe
    logs_dir = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Crear handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Crear handler para archivo de logs general
    general_log_file = os.path.join(logs_dir, "app.log")
    file_handler = RotatingFileHandler(
        general_log_file, 
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Crear handler para archivo de logs de errores
    error_log_file = os.path.join(logs_dir, "error.log")
    error_file_handler = RotatingFileHandler(
        error_log_file, 
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    logger.addHandler(error_file_handler)
    
    # Crear handler para logs de servicios (como data_lookup)
    services_log_file = os.path.join(logs_dir, "services.log")
    services_file_handler = RotatingFileHandler(
        services_log_file, 
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    services_file_handler.setFormatter(formatter)
    services_logger = logging.getLogger("app.services")
    services_logger.propagate = True  # Los logs también van al logger principal
    services_logger.addHandler(services_file_handler)
    
    # Configurar loggers de terceros
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    return logger

# Crear el logger principal
logger = setup_logging() 
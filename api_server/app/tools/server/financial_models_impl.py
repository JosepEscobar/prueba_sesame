from typing import Dict, Any, List, Optional
import time
import random
import os
import json
from pathlib import Path

from app.core.logging import logger
from app.tools.implementations.financial_models import FinancialModelsImplementation

class FinancialModelsMCPTool:
    """
    Implementación de la herramienta financial_models para el servidor MCP.
    
    Adapta la implementación existente para que sea compatible con el servidor MCP.
    """
    
    def __init__(self, schema_path: Optional[str] = None):
        """
        Inicializa la herramienta financial_models para MCP.
        
        Args:
            schema_path: Ruta al archivo JSON del esquema (opcional)
        """
        # Cargar la implementación existente
        self.implementation = FinancialModelsImplementation()
        
        # Cargar el esquema si se proporciona
        self.schema = None
        if schema_path:
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    self.schema = json.load(f)
            except Exception as e:
                logger.error(f"Error al cargar esquema de financial_models: {str(e)}")
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Obtiene el esquema de la herramienta.
        
        Returns:
            Esquema de la herramienta en formato JSON
        """
        if self.schema:
            return self.schema
        
        # Esquema predeterminado si no se cargó desde archivo
        return {
            "name": "financial_models",
            "description": "Obtiene modelos o plantillas financieras apropiadas para diferentes escenarios empresariales.",
            "inputs": {
                "type": "object",
                "properties": {
                    "model_type": {
                        "type": "string", 
                        "description": "Tipo de modelo financiero",
                        "enum": [
                            "cash_flow", 
                            "valuation", 
                            "budget", 
                            "forecast", 
                            "investment", 
                            "pricing", 
                            "breakeven", 
                            "roi"
                        ]
                    },
                    "industry": {
                        "type": "string", 
                        "description": "Industria específica para el modelo", 
                        "default": "general"
                    },
                    "complexity": {
                        "type": "string", 
                        "description": "Nivel de complejidad del modelo", 
                        "enum": ["basic", "intermediate", "advanced"], 
                        "default": "intermediate"
                    },
                    "format": {
                        "type": "string", 
                        "description": "Formato de salida deseado", 
                        "enum": ["excel", "google_sheets", "pdf"], 
                        "default": "excel"
                    }
                },
                "required": ["model_type"]
            },
            "outputs": {
                "type": "object",
                "properties": {
                    "models": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Nombre del modelo financiero"},
                                "description": {"type": "string", "description": "Descripción del modelo"},
                                "format": {"type": "string", "description": "Formato del modelo (Excel, PDF, etc.)"},
                                "complexity": {"type": "string", "description": "Nivel de complejidad"},
                                "creator": {"type": "string", "description": "Creador o fuente del modelo"},
                                "last_updated": {"type": "string", "description": "Fecha de última actualización"},
                                "download_url": {"type": "string", "description": "URL para descargar el modelo"},
                                "preview_url": {"type": "string", "description": "URL para previsualizar el modelo"},
                                "tags": {"type": "array", "items": {"type": "string"}, "description": "Etiquetas relacionadas"}
                            }
                        }
                    },
                    "recommendations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "model_id": {"type": "string", "description": "ID del modelo recomendado"},
                                "reason": {"type": "string", "description": "Razón de la recomendación"}
                            }
                        }
                    },
                    "total_results": {"type": "integer", "description": "Número total de modelos disponibles"}
                }
            }
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la herramienta financial_models.
        
        Args:
            params: Parámetros para la herramienta
            
        Returns:
            Resultado de la ejecución
        """
        return self.implementation.get_models(params) 
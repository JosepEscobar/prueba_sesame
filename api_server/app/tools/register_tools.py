"""
Script para registrar todas las implementaciones de herramientas en el sistema.
"""

from typing import List, Dict, Any, Optional
import os
import json
from pathlib import Path
import importlib
import asyncio

from langchain.tools import BaseTool, StructuredTool
from pydantic import BaseModel, create_model

from app.core.logging import logger
from app.core.metrics import metrics
from app.core.config import get_settings
from app.tools.mcp_client import MCPClient
from app.tools.server.server_init import init_mcp_server
from app.tools.tool_registry import tool_registry
from app.tools.implementations.financial_models import FinancialModelsImplementation

# Obtener la configuración
settings = get_settings()

def load_tools_from_schemas():
    """
    Carga herramientas desde esquemas JSON locales y las registra en el sistema.
    
    Esta función puede ser utilizada durante la inicialización para asegurar
    que todas las herramientas estén disponibles para los agentes.
    """
    try:
        # Rutas para los ficheros de descripción de herramientas en formato JSON Schema
        schema_dir = Path(__file__).parent / "schemas"
        
        # Verificar que el directorio existe
        if not schema_dir.exists():
            logger.warning(f"El directorio de schemas no existe: {schema_dir}")
            return
        
        # Cargar todos los schemas JSON en el directorio
        for schema_file in schema_dir.glob("*.json"):
            try:
                with open(schema_file, "r") as f:
                    schema = json.load(f)
                
                # Extraer información del schema
                name = schema.get("name", schema_file.stem)
                description = schema.get("description", "")
                category = schema.get("category", "general")
                
                # Crear una herramienta basada en el esquema
                _register_schema_tool(name, description, schema, category)
                logger.info(f"Herramienta local cargada: {name}")
                
            except Exception as e:
                logger.error(f"Error cargando schema {schema_file}: {str(e)}")
    except Exception as e:
        logger.error(f"Error cargando schemas: {str(e)}")

def _register_schema_tool(name: str, description: str, schema: Dict[str, Any], category: str):
    """
    Registra una herramienta basada en un schema JSON.
    
    Args:
        name: Nombre de la herramienta
        description: Descripción de la herramienta
        schema: Schema JSON que define la herramienta
        category: Categoría de la herramienta
    """
    try:
        # Crear un modelo Pydantic dinámico para los argumentos de entrada
        input_props = schema.get("properties", {})
        fields = {}
        
        for prop_name, prop_details in input_props.items():
            prop_type = prop_details.get("type", "string")
            prop_description = prop_details.get("description", "")
            
            # Mapear tipos JSON Schema a tipos Python
            python_type = str
            if prop_type == "number":
                python_type = float
            elif prop_type == "integer":
                python_type = int
            elif prop_type == "boolean":
                python_type = bool
            elif prop_type == "array":
                python_type = List[str]
            elif prop_type == "object":
                python_type = Dict[str, Any]
            
            # Añadir el campo al modelo
            fields[prop_name] = (Optional[python_type], None)
        
        # Crear el modelo dinámico
        input_model = create_model(
            f"{name}Input",
            **fields
        )
        
        # Función que implementa la herramienta
        def tool_func(**kwargs):
            try:
                # Registrar inicio de ejecución para métricas
                with metrics.tool_execution_time.labels(tool_name=name).time():
                    # Implementación simulada para demostración
                    logger.info(f"Ejecutando herramienta {name} con parámetros: {kwargs}")
                    
                    # Si existe una implementación real, la cargamos y ejecutamos
                    impl_module_name = schema.get("implementation", "")
                    if impl_module_name:
                        try:
                            module_path, class_name = impl_module_name.rsplit(".", 1)
                            module = importlib.import_module(module_path)
                            impl_class = getattr(module, class_name)
                            
                            # Instanciar e invocar
                            impl = impl_class()
                            result = impl.execute(**kwargs)
                            metrics.tool_calls_total.labels(
                                tool_name=name, 
                                status="success"
                            ).inc()
                            return result
                        except Exception as e:
                            logger.error(f"Error en implementación de {name}: {str(e)}")
                            metrics.tool_calls_total.labels(
                                tool_name=name, 
                                status="error"
                            ).inc()
                            return {"error": f"Error en implementación: {str(e)}"}
                    
                    # Si no hay implementación, devolvemos datos simulados
                    metrics.tool_calls_total.labels(
                        tool_name=name, 
                        status="success"
                    ).inc()
                    return {
                        "result": f"Simulación de resultados para {name}",
                        "params": kwargs
                    }
            except Exception as e:
                metrics.tool_calls_total.labels(
                    tool_name=name, 
                    status="error"
                ).inc()
                logger.error(f"Error ejecutando herramienta {name}: {str(e)}")
                return {"error": str(e)}
        
        # Crear una herramienta estructurada
        tool = StructuredTool.from_function(
            func=tool_func,
            name=name,
            description=description,
            args_schema=input_model
        )
        
        # Registrar en el sistema global de LangChain
        from langchain.tools import tool as langchain_tool_decorator
        
        # Usar el decorador sin proporcionar name directamente
        decorated_tool = langchain_tool_decorator(description=description)(tool_func)
        decorated_tool.__name__ = name
        
        logger.info(f"Herramienta {name} registrada como herramienta de LangChain")
    except Exception as e:
        logger.error(f"Error registrando herramienta {name}: {str(e)}")

def register_all_tools():
    """
    Registra todas las implementaciones de herramientas disponibles en el sistema.
    
    Esta función debe ser llamada durante la inicialización de la aplicación
    para asegurar que todas las herramientas estén disponibles para los agentes.
    """
    logger.info("Iniciando registro de implementaciones de herramientas...")
    
    try:
        # Cargar herramientas desde esquemas JSON
        load_tools_from_schemas()
        
        # Registrar implementación de financial_models
        financial_models_impl = FinancialModelsImplementation()
        
        # Crear una herramienta estructurada para financial_models
        financial_tool = StructuredTool.from_function(
            func=financial_models_impl.get_models,
            name="financial_models",
            description="Obtiene modelos o plantillas financieras para diferentes industrias"
        )
        
        # Registrar en el sistema global de LangChain
        from langchain.tools import tool as langchain_tool_decorator
        
        # Usar el decorador sin proporcionar name directamente
        decorated_tool = langchain_tool_decorator(
            description="Obtiene modelos o plantillas financieras para diferentes industrias"
        )(financial_models_impl.get_models)
        decorated_tool.__name__ = "financial_models"
        
        logger.info("Implementación de financial_models registrada correctamente")
        
        # Registrar cliente MCP para otras herramientas
        asyncio.create_task(_register_mcp_tools())
        
        # Mostrar resumen de herramientas
        logger.info(f"Registro inicial de herramientas completado")
        
        return {
            "status": "success",
            "implemented_tools": 3,  # Ajustar según el número real de herramientas implementadas
            "total_tools": 3         # Ajustar según el número total de herramientas disponibles
        }
    except Exception as e:
        logger.error(f"Error en registro de herramientas: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "implemented_tools": 0,
            "total_tools": 0
        }

async def _register_mcp_tools():
    """
    Registra herramientas disponibles a través del cliente MCP.
    
    Esta función asíncrona se ejecuta en segundo plano para no bloquear
    la inicialización de la aplicación.
    """
    try:
        # Inicializar el cliente MCP
        mcp_client = MCPClient()
        initialized = await mcp_client.initialize()
        
        if not initialized:
            logger.warning("No se pudo inicializar el cliente MCP, las herramientas MCP no estarán disponibles")
            return
        
        # Registrar las herramientas disponibles en el servidor MCP
        try:
            # Obtener herramientas directamente del método asíncrono
            tools = []
            try:
                # Usar try/except específico para el método list_tools_async
                tools = await mcp_client.list_tools_async()
            except Exception as e:
                logger.error(f"Error específico al listar herramientas MCP de forma asíncrona: {str(e)}")
                # Intentar de forma alternativa
                tools = mcp_client.list_tools()
            
            if tools is None:
                tools = []
                
            logger.info(f"Herramientas disponibles en el servidor MCP: {len(tools)}")
            
            for tool_info in tools:
                try:
                    tool_name = tool_info.get("name")
                    tool_description = tool_info.get("description", "")
                    
                    # Creamos una función closure para cada herramienta específica
                    # para mantener el contexto de tool_name
                    def create_tool_func(specific_tool_name):
                        # Función síncrona que llama a la herramienta MCP
                        def tool_func(**kwargs):
                            try:
                                # Registrar inicio de ejecución para métricas
                                with metrics.tool_execution_time.labels(tool_name=specific_tool_name).time():
                                    logger.info(f"Ejecutando herramienta MCP {specific_tool_name} con parámetros: {kwargs}")
                                    
                                    # Llamar a la herramienta en el servidor MCP de forma síncrona
                                    result = mcp_client.call_tool_sync(specific_tool_name, kwargs)
                                    
                                    metrics.tool_calls_total.labels(
                                        tool_name=specific_tool_name, 
                                        status="success"
                                    ).inc()
                                    
                                    return result
                            except Exception as e:
                                metrics.tool_calls_total.labels(
                                    tool_name=specific_tool_name, 
                                    status="error"
                                ).inc()
                                logger.error(f"Error ejecutando herramienta MCP {specific_tool_name}: {str(e)}")
                                return {"error": str(e)}
                        
                        return tool_func
                    
                    # Registrar la herramienta en LangChain
                    from langchain.tools import tool as langchain_tool_decorator
                    
                    # Usar el decorador sin proporcionar name directamente
                    func = create_tool_func(tool_name)
                    decorated_tool = langchain_tool_decorator(
                        description=tool_description
                    )(func)
                    decorated_tool.__name__ = tool_name
                    
                    logger.info(f"Herramienta MCP registrada: {tool_name}")
                    
                except Exception as e:
                    logger.error(f"Error registrando herramienta MCP {tool_info.get('name', 'desconocida')}: {str(e)}")
        except Exception as e:
            logger.error(f"Error al listar herramientas MCP: {str(e)}")
            tools = []
    except Exception as e:
        logger.error(f"Error al registrar herramientas MCP: {str(e)}")
        return 
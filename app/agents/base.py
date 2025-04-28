from typing import Dict, Any, List, Optional, Callable
import time
import abc
from langchain_openai import ChatOpenAI
from app.core.logging import logger
from app.core.metrics import MetricsCollector
from app.core.config import get_settings

settings = get_settings()

class BaseAgent(abc.ABC):
    """
    Clase base para todos los agentes del sistema.
    
    Define la interfaz y funcionalidad común que deben implementar
    todos los agentes, incluyendo ejecución, gestión de herramientas y
    manejo de memoria.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Inicializa un agente base.
        
        Args:
            name: Nombre único del agente
            description: Descripción breve de la función del agente
        """
        self.name = name
        self.description = description
        self.tools = {}
        self.memory = {}
        
        # Inicializar el modelo LLM predeterminado
        self.llm = ChatOpenAI(
            model_name=settings.OPENAI_MODEL,
            temperature=settings.TEMPERATURE,
            api_key=settings.OPENAI_API_KEY
        )
        
        logger.info(f"Agente {name} inicializado")
    
    def add_tool(self, tool_name: str, tool: Any) -> None:
        """
        Añade una herramienta al agente para su uso durante la ejecución.
        
        Args:
            tool_name: Nombre único para la herramienta
            tool: La herramienta (función, clase o objeto) a añadir
        """
        self.tools[tool_name] = tool
        logger.info(f"Herramienta '{tool_name}' añadida al agente {self.name}")
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """
        Obtiene una herramienta por su nombre.
        
        Args:
            tool_name: Nombre de la herramienta a obtener
            
        Returns:
            La herramienta solicitada o None si no existe
        """
        return self.tools.get(tool_name)
    
    def update_memory(self, key: str, value: Any) -> None:
        """
        Actualiza la memoria del agente con un nuevo valor.
        
        Args:
            key: Clave para acceder al valor en la memoria
            value: Valor a almacenar
        """
        self.memory[key] = value
        logger.debug(f"Memoria actualizada para agente {self.name}: {key}")
    
    def get_memory(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de la memoria del agente.
        
        Args:
            key: Clave del valor a obtener
            default: Valor por defecto si la clave no existe
            
        Returns:
            Valor asociado a la clave o el valor por defecto
        """
        return self.memory.get(key, default)
    
    def execute(self, input_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Ejecuta la lógica principal del agente.
        
        Esta es una implementación base que gestiona métricas, logging y 
        manejo de errores. Cada agente específico debe implementar _execute_impl.
        
        Args:
            input_data: Diccionario con los datos de entrada para el agente
            
        Returns:
            Diccionario con los resultados de la ejecución
        """
        start_time = time.time()
        
        try:
            logger.info(f"Iniciando ejecución de agente {self.name}")
            
            # Ejecutar la implementación específica del agente
            result = self._execute_impl(input_data)
            
            # Registrar métricas
            execution_time = time.time() - start_time
            MetricsCollector.record_agent_execution(
                agent_name=self.name,
                execution_time=execution_time,
                status="success"
            )
            
            # Registrar confianza si está disponible
            if "confidence" in result:
                MetricsCollector.record_agent_confidence(
                    agent_name=self.name,
                    confidence=result["confidence"]
                )
            
            # Registrar uso de tokens si está disponible
            if "token_usage" in result:
                MetricsCollector.record_token_usage(
                    agent_name=self.name,
                    model=result.get("model", "unknown"),
                    tokens=result["token_usage"]
                )
            
            logger.info(f"Agente {self.name} completó ejecución en {execution_time:.2f} segundos")
            
            return result
            
        except Exception as e:
            # Registrar el error
            execution_time = time.time() - start_time
            logger.error(f"Error en agente {self.name}: {str(e)}")
            
            # Registrar métricas de error
            MetricsCollector.record_agent_execution(
                agent_name=self.name,
                execution_time=execution_time,
                status="error"
            )
            
            MetricsCollector.record_error(
                agent_name=self.name,
                error_type=type(e).__name__
            )
            
            # Devolver respuesta de error
            return {
                "error": str(e),
                "confidence": 0.0,
                "input": input_data
            }
    
    @abc.abstractmethod
    def _execute_impl(self, input_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Implementación específica de la ejecución del agente.
        
        Debe ser implementada por cada agente concreto.
        
        Args:
            input_data: Diccionario con los datos de entrada para el agente
            
        Returns:
            Diccionario con los resultados de la ejecución
        """
        pass
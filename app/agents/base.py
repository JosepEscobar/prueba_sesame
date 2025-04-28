from typing import Dict, Any, List
import time
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from app.core.config import get_settings
from app.core.logging import logger
from app.core.metrics import MetricsCollector

settings = get_settings()

class BaseAgent:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.llm = ChatOpenAI(
            model_name=settings.OPENAI_MODEL,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
            api_key=settings.OPENAI_API_KEY
        )
        self.tools: List[Any] = []
        self.memory: Dict[str, Any] = {}
        
        logger.info(
            f"Agente inicializado: {name}",
            extra={
                "agent_name": name,
                "description": description
            }
        )
        
    def add_tool(self, tool: Any) -> None:
        """Añade una herramienta al agente."""
        self.tools.append(tool)
        logger.info(
            f"Herramienta añadida al agente {self.name}",
            extra={
                "agent_name": self.name,
                "tool_name": tool.__class__.__name__
            }
        )
        
    def update_memory(self, key: str, value: Any) -> None:
        """Actualiza la memoria del agente."""
        self.memory[key] = value
        logger.debug(
            f"Memoria actualizada para el agente {self.name}",
            extra={
                "agent_name": self.name,
                "memory_key": key
            }
        )
        
    def get_memory(self, key: str) -> Any:
        """Obtiene un valor de la memoria del agente."""
        return self.memory.get(key)
        
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Método base para la ejecución del agente. Debe ser implementado por las clases hijas."""
        start_time = time.time()
        
        try:
            logger.info(
                f"Ejecutando agente: {self.name}",
                extra={
                    "agent_name": self.name,
                    "input_data": input_data
                }
            )
            
            # Llamar al método específico de la clase hija
            result = self._execute_impl(input_data)
            
            # Calcular tiempo de ejecución
            execution_time = time.time() - start_time
            
            # Registrar métricas
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
                    model=settings.OPENAI_MODEL,
                    token_count=result["token_usage"]
                )
            
            logger.info(
                f"Agente {self.name} ejecutado con éxito",
                extra={
                    "agent_name": self.name,
                    "execution_time": execution_time,
                    "confidence": result.get("confidence", 0)
                }
            )
            
            return result
            
        except Exception as e:
            # Calcular tiempo de ejecución
            execution_time = time.time() - start_time
            
            # Registrar error
            MetricsCollector.record_agent_execution(
                agent_name=self.name,
                execution_time=execution_time,
                status="error"
            )
            
            MetricsCollector.record_error(
                agent_name=self.name,
                error_type=e.__class__.__name__
            )
            
            logger.error(
                f"Error en agente {self.name}: {str(e)}",
                extra={
                    "agent_name": self.name,
                    "error": str(e),
                    "execution_time": execution_time
                }
            )
            
            raise
    
    def _execute_impl(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Implementación específica del método execute. Debe ser implementado por las clases hijas."""
        raise NotImplementedError("Los agentes deben implementar el método _execute_impl") 
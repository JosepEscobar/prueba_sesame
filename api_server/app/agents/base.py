from typing import Dict, Any, List, Optional, Callable
import time
import abc
import os
import json
from app.core.logging import logger
from app.core.metrics import MetricsCollector
from app.core.config import get_settings
from langchain_openai import ChatOpenAI

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
        
        # Inicializar modelos y clientes
        self.llm = None
        self.client = None
        
        # Verificar si hay una API key de OpenAI válida configurada
        if settings.is_openai_api_key_valid():
            try:
                # Importar el cliente directamente para mayor control
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                
                # Log para depuración
                logger.info(f"Inicializando cliente OpenAI para {name} con API KEY: {settings.OPENAI_API_KEY[:5]}...{settings.OPENAI_API_KEY[-5:] if len(settings.OPENAI_API_KEY) > 10 else ''}")
                
                # No hacemos la verificación de conexión aquí para ahorrar llamadas a la API
                # y evitar errores 429 (Too Many Requests)
                logger.info(f"Cliente OpenAI configurado para agente {name}")
                
                # Inicializar el LLM de LangChain sin verificación previa
                try:
                    self.llm = ChatOpenAI(
                        model_name=settings.OPENAI_MODEL,
                        temperature=settings.TEMPERATURE,
                        api_key=settings.OPENAI_API_KEY,
                        max_tokens=settings.MAX_TOKENS
                    )
                    logger.info(f"LLM de LangChain inicializado correctamente para agente {name}")
                except Exception as e:
                    logger.warning(f"No se pudo inicializar LangChain para {name}, usando cliente directo: {str(e)}")
                    logger.info(f"Cliente OpenAI directo asignado a agente {name}")
            except Exception as e:
                logger.warning(f"No se pudo inicializar OpenAI para agente {name}: {str(e)}")
                self.client = None
        else:
            logger.warning(f"No hay API key válida configurada para {name}")
        
        logger.info(f"Agente {name} inicializado")
    
    def log_llm_call(self, prompt: Any, response: Any, prompt_type: str = "langchain"):
        """
        Registra un prompt enviado al LLM y la respuesta recibida.
        
        Args:
            prompt: El prompt enviado al LLM
            response: La respuesta recibida del LLM
            prompt_type: El tipo de prompt ("langchain", "openai_direct" u otro)
        """
        try:
            # Registrar información según el tipo de prompt
            if prompt_type == "langchain":
                # Para mensajes de LangChain
                if hasattr(prompt, "__iter__"):
                    # Si es una lista de mensajes
                    prompt_str = "\n---\n".join([
                        f"[{msg.type}]: {msg.content}" 
                        for msg in prompt if hasattr(msg, "type") and hasattr(msg, "content")
                    ])
                else:
                    prompt_str = str(prompt)
                
                response_str = response.content if hasattr(response, "content") else str(response)
            
            elif prompt_type == "openai_direct":
                # Para llamadas directas a la API de OpenAI
                messages = prompt.get("messages", [])
                prompt_str = "\n---\n".join([
                    f"[{msg.get('role', 'unknown')}]: {msg.get('content', '')}" 
                    for msg in messages
                ])
                
                if hasattr(response, "choices") and len(response.choices) > 0:
                    response_str = response.choices[0].message.content
                else:
                    response_str = str(response)
            else:
                # Para otros tipos de prompts
                prompt_str = str(prompt)
                response_str = str(response)
            
            # Truncar si son demasiado largos para el log
            max_log_len = 1000  # Caracteres máximos para el log
            if len(prompt_str) > max_log_len:
                prompt_str = prompt_str[:max_log_len] + f"... [truncado, longitud total: {len(prompt_str)}]"
            if len(response_str) > max_log_len:
                response_str = response_str[:max_log_len] + f"... [truncado, longitud total: {len(response_str)}]"
            
            # Registrar en el log
            logger.info(f"[{self.name}] LLM Prompt ({prompt_type}):\n{prompt_str}")
            logger.info(f"[{self.name}] LLM Respuesta:\n{response_str}")
            
            # Registrar uso de tokens si está disponible
            if hasattr(response, "usage") and response.usage:
                token_usage = response.usage
                logger.info(f"[{self.name}] Uso de tokens: {token_usage}")
                
        except Exception as e:
            logger.error(f"Error al registrar llamada al LLM: {str(e)}")

    def invoke_llm(self, prompt: Any, prompt_type: str = "langchain", **kwargs):
        """
        Invoca el LLM y registra la llamada.
        
        Args:
            prompt: El prompt a enviar al LLM
            prompt_type: El tipo de prompt
            **kwargs: Argumentos adicionales para la llamada al LLM
            
        Returns:
            La respuesta del LLM
        """
        response = None
        
        try:
            # Invocar según el tipo de LLM disponible
            if prompt_type == "langchain" and self.llm is not None:
                response = self.llm.invoke(prompt, **kwargs)
            elif prompt_type == "openai_direct" and self.client is not None:
                response = self.client.chat.completions.create(**prompt, **kwargs)
            else:
                raise ValueError(f"No hay LLM disponible para el tipo de prompt {prompt_type}")
                
            # Registrar la llamada
            self.log_llm_call(prompt, response, prompt_type)
            
            return response
        except Exception as e:
            logger.error(f"Error al invocar LLM: {str(e)}")
            raise e
    
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
from typing import Dict, Any, List
from langchain.agents import AgentExecutor
from langchain.chat_models import ChatOpenAI
from app.core.config import get_settings

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
        
    def add_tool(self, tool: Any) -> None:
        """Añade una herramienta al agente."""
        self.tools.append(tool)
        
    def update_memory(self, key: str, value: Any) -> None:
        """Actualiza la memoria del agente."""
        self.memory[key] = value
        
    def get_memory(self, key: str) -> Any:
        """Obtiene un valor de la memoria del agente."""
        return self.memory.get(key)
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Método base para la ejecución del agente. Debe ser implementado por las clases hijas."""
        raise NotImplementedError("Los agentes deben implementar el método execute") 
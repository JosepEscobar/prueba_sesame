from typing import Dict, Any
from langchain.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent

class ActionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Action Agent",
            description="Agente especializado en realizar acciones específicas"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un agente especializado en realizar acciones específicas.
            Tu objetivo es ejecutar tareas concretas y proporcionar resultados tangibles.
            
            Debes:
            1. Identificar la acción requerida
            2. Planificar los pasos necesarios
            3. Ejecutar la acción de manera eficiente
            4. Proporcionar un reporte detallado del resultado
            
            Formatea tu respuesta incluyendo:
            - Acción realizada
            - Pasos ejecutados
            - Resultado obtenido
            - Recomendaciones posteriores"""),
            ("human", "{input}")
        ])
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la acción solicitada."""
        # Preparar el input para el prompt
        prompt_input = {
            "input": input_data.get("action_request", "")
        }
        
        # Obtener la respuesta del LLM
        chain = self.prompt | self.llm
        response = await chain.ainvoke(prompt_input)
        
        return {
            "action_result": response.content,
            "original_input": input_data,
            "confidence": 0.85
        } 
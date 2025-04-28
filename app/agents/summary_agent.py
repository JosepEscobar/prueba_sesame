from typing import Dict, Any
from langchain.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent

class SummaryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Summary Agent",
            description="Agente especializado en crear resúmenes concisos"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un agente especializado en crear resúmenes concisos y efectivos.
            Tu objetivo es extraer la información más relevante y presentarla de manera clara y concisa.
            
            Debes:
            1. Identificar los puntos clave
            2. Eliminar información redundante
            3. Mantener la coherencia del contenido
            4. Asegurar que el resumen sea completo y preciso
            
            El resumen debe ser:
            - Conciso y directo
            - Bien estructurado
            - Fácil de entender
            - Mantener el contexto esencial"""),
            ("human", "{input}")
        ])
        
    async def _execute_impl(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la creación del resumen."""
        # Preparar el input para el prompt
        prompt_input = {
            "input": input_data.get("content", "")
        }
        
        # Obtener la respuesta del LLM
        chain = self.prompt | self.llm
        response = await chain.ainvoke(prompt_input)
        
        return {
            "summary": response.content,
            "original_input": input_data,
            "confidence": 0.95
        } 
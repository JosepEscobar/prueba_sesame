from typing import Dict, Any
from langchain.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent

class RouterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Router Agent",
            description="Agente que decide qué agente especializado debe manejar la solicitud"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un agente router que decide qué agente especializado debe manejar una solicitud.
            Analiza la solicitud y decide el agente más apropiado basado en su descripción y capacidades.
            
            Agentes disponibles:
            - Agente de Análisis: Para análisis detallado de datos y textos
            - Agente de Acción: Para realizar acciones específicas
            - Agente de Resumen: Para crear resúmenes concisos
            
            Responde con el nombre del agente más apropiado y una breve explicación."""),
            ("human", "{input}")
        ])
        
    async def _execute_impl(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el proceso de enrutamiento."""
        # Preparar el input para el prompt
        prompt_input = {
            "input": input_data.get("query", "")
        }
        
        # Obtener la respuesta del LLM
        chain = self.prompt | self.llm
        response = await chain.ainvoke(prompt_input)
        
        # Procesar la respuesta para determinar el agente
        agent_decision = response.content
        
        return {
            "agent_decision": agent_decision,
            "original_input": input_data,
            "confidence": 0.8  # Esto debería ser calculado basado en la respuesta
        } 
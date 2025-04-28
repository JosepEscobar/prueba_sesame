from typing import Dict, Any
from langchain.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent

class AnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Analysis Agent",
            description="Agente especializado en análisis detallado de datos y textos"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un agente especializado en análisis detallado de datos y textos.
            Tu objetivo es proporcionar análisis profundos, identificar patrones, y extraer insights valiosos.
            
            Debes:
            1. Analizar el contenido en detalle
            2. Identificar patrones y tendencias
            3. Extraer conclusiones relevantes
            4. Proporcionar recomendaciones basadas en el análisis
            
            Formatea tu respuesta de manera clara y estructurada."""),
            ("human", "{input}")
        ])
        
    async def _execute_impl(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el análisis del contenido proporcionado."""
        # Preparar el input para el prompt
        prompt_input = {
            "input": input_data.get("content", "")
        }
        
        # Obtener la respuesta del LLM
        chain = self.prompt | self.llm
        response = await chain.ainvoke(prompt_input)
        
        return {
            "analysis": response.content,
            "original_input": input_data,
            "confidence": 0.9
        } 
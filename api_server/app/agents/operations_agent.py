import time
from typing import Any

from app.agents.base import BaseAgent
from app.core.logging import logger


class OperationsAgent(BaseAgent):
    """
    Agente especializado en operaciones y gestión operativa.
    
    Este agente proporciona recomendaciones y análisis sobre:
    - Optimización de procesos empresariales
    - Gestión de la cadena de suministro
    - Planificación de capacidad y recursos
    - Análisis de eficiencia operativa
    - Gestión de inventario y logística
    - Implementación de sistemas de gestión de calidad
    - Automatización de procesos
    - Mejora continua (Lean, Six Sigma)
    - Gestión de proyectos operativos
    - Estrategias de reducción de costos operativos
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "operations_agent"
        self.description = "Especialista en gestión operativa y optimización de procesos"
        logger.info(f"Agente de operaciones inicializado: {self.name}")

    def _execute_impl(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Implementación de la ejecución del agente de operaciones.
        
        Args:
            input_data: Diccionario con los datos de entrada, incluyendo 'query' y opcionalmente 'content'
            
        Returns:
            Diccionario con el resultado del procesamiento
        """
        start_time = time.time()

        # Preparar entrada para el prompt
        query = input_data.get('query', '')
        content = input_data.get('content', '')

        # Loguear la consulta con un límite seguro
        query_preview = query[:100] + "..." if len(query) > 100 else query
        logger.info(f"Procesando consulta de operaciones: {query_preview}")

        # Preparar el sistema de prompt para obtener una respuesta estructurada
        prompt = f"""
        Como especialista en operaciones y gestión operativa, analiza la siguiente consulta y proporciona recomendaciones estratégicas:
        
        CONSULTA: {query}
        
        CONTEXTO ADICIONAL: {content}
        
        Considera los siguientes aspectos en tu análisis:
        1. Estado actual de los procesos operativos
        2. Cuellos de botella y áreas de ineficiencia
        3. Oportunidades de optimización y automatización
        4. Gestión de recursos y capacidad
        5. Integración de tecnología en operaciones
        6. Métricas operativas clave a monitorear
        7. Impacto ambiental y sostenibilidad operativa
        
        Tu respuesta debe ser práctica y orientada a resultados, incluyendo:
        - Análisis detallado de la situación operativa actual
        - Identificación de problemas operativos específicos
        - Recomendaciones de mejora priorizadas
        - Metodologías y herramientas relevantes (Lean, Six Sigma, etc.)
        - Plan de implementación con fases claras
        - Métricas de éxito y KPIs operativos
        - Consideraciones sobre gestión del cambio
        
        Utiliza terminología precisa de gestión de operaciones, referencias a mejores prácticas y metodologías estándar del sector.
        """

        try:
            # Invocar el modelo de lenguaje
            response = self.invoke_llm(prompt)

            # Calcular tiempo de procesamiento
            processing_time = time.time() - start_time
            logger.info(f"Consulta de operaciones procesada en {processing_time:.2f} segundos")

            # Establecer un nivel de confianza (puede ser ajustado según criterios específicos)
            confidence = 0.89  # Nivel de confianza para respuestas operativas

            return {
                "result": response,
                "query": query,
                "confidence": confidence
            }

        except Exception as e:
            logger.error(f"Error al procesar consulta de operaciones: {str(e)}")
            return {
                "result": f"Error al procesar la consulta de operaciones: {str(e)}",
                "query": query,
                "confidence": 0.0
            }

import json
import re
import time
from typing import Any

from app.agents.base import BaseAgent
from app.core.config import get_settings
from app.core.llm import get_llm_client
from app.core.logging import logger
from app.core.metrics import MetricsCollector

settings = get_settings()

class GuardrailAgent(BaseAgent):
    """
    Agente guardrail que actúa como filtro inicial para determinar si una consulta
    está dentro del ámbito de servicios ofrecidos por el sistema.
    
    Utiliza un modelo LLM para analizar inteligentemente si la consulta está dentro
    del ámbito, en lugar de usar un sistema rígido de palabras clave.
    """

    def __init__(self):
        """Inicializa el agente guardrail."""
        super().__init__(
            name="guardrail_agent",
            description="Agente que determina si una consulta está dentro del ámbito de servicios ofrecidos utilizando LLM."
        )

        # Obtener el cliente LLM
        self.llm_client = get_llm_client()

        # Dominios principales del sistema
        self.domains = [
            "finanzas y análisis financiero",
            "marketing y estrategias de mercado",
            "análisis de datos empresariales",
            "estrategia y gestión empresarial"
        ]

        # Definición del ámbito de la aplicación
        self.scope_definition = """
        La aplicación Sesame proporciona asistencia empresarial en estos dominios:
        
        1. Finanzas y análisis financiero:
           - Análisis de estados financieros (balance, P&G, flujo de caja)
           - Cálculo y análisis de ratios financieros
           - Valoración de empresas y activos
           - Proyecciones financieras
           - Análisis de rentabilidad
           - Gestión de costos y presupuestos
        
        2. Marketing y estrategias de mercado:
           - Análisis de campañas de marketing
           - Evaluación de estrategias de marketing digital
           - Segmentación y análisis de mercado
           - Evaluación de rendimiento publicitario
           - Planificación de campañas
           - Análisis de conversión y engagement
        
        3. Análisis de datos empresariales:
           - Análisis de tendencias en datos de negocio
           - Identificación de patrones en datos empresariales
           - Preparación de informes y dashboards
           - Benchmarking y comparativas sectoriales
           - Análisis predictivos básicos
        
        4. Estrategia y gestión empresarial:
           - Planificación estratégica
           - Optimización de procesos de negocio
           - Análisis de rendimiento operativo
           - Gestión de recursos empresariales
           - Evaluación de oportunidades de negocio
        """

        # Servicios específicos ofrecidos
        self.services = [
            "Análisis financiero y modelos de proyección económica",
            "Estrategias de marketing y análisis de campañas",
            "Análisis de datos empresariales y tendencias de mercado",
            "Optimización de operaciones y procesos de negocio",
            "Valoración de empresas y activos financieros",
            "Estudios de mercado y análisis competitivo",
            "Planificación estratégica de negocios"
        ]

        # Temas explícitamente excluidos
        self.explicitly_excluded_topics = [
            "política", "religión", "contenido para adultos", "armas", "drogas ilegales",
            "juegos de azar", "medicina", "diagnóstico médico", "psicología", "terapia",
            "asesoramiento legal", "hacking", "actividades ilegales", "contenido ofensivo",
            "violencia", "discriminación", "creación de contenido ilegal", "acoso"
        ]

    def _check_explicitly_excluded(self, query: str) -> str | None:
        """
        Verifica si la consulta contiene temas explícitamente excluidos.
        
        Args:
            query: La consulta a verificar
            
        Returns:
            Mensaje de exclusión si contiene un tema excluido, None en caso contrario
        """
        query_lower = query.lower()
        for topic in self.explicitly_excluded_topics:
            if topic in query_lower:
                return f"Lo siento, no podemos proporcionar información sobre {topic}."
        return None

    def _evaluate_with_llm(self, query: str) -> dict[str, Any]:
        """
        Evalúa la consulta utilizando un modelo LLM para determinar si está dentro del ámbito.
        
        Args:
            query: La consulta a evaluar
            
        Returns:
            Resultado de la evaluación
        """
        prompt = f"""
        # Tarea: Evaluación de consulta para determinar si está dentro del ámbito de servicios
        
        ## Ámbito del sistema
        {self.scope_definition}
        
        ## Consulta a evaluar
        "{query}"
        
        ## Instrucciones
        1. Determina si la consulta está relacionada con alguno de los dominios de la aplicación.
        2. Si está en el ámbito, identifica el dominio más relevante y explica por qué.
        3. Si no está en el ámbito, explica claramente por qué y sugiere cómo reformular la consulta para que esté dentro del ámbito.
        
        ## Formato de respuesta
        Proporciona tu respuesta en formato JSON con los siguientes campos:
        - "in_scope": boolean (true/false)
        - "domain": string (el dominio más relevante si está en el ámbito)
        - "confidence": float (0.0-1.0, tu nivel de confianza en la evaluación)
        - "reasoning": string (tu razonamiento detallado)
        - "explanation": string (explicación para el usuario)
        """

        try:
            response = self.llm_client.generate_text(prompt)

            # Intentar extraer el JSON de la respuesta
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Buscar cualquier estructura que parezca JSON
                json_str = re.search(r'(\{.*\})', response, re.DOTALL)
                if json_str:
                    json_str = json_str.group(1)
                else:
                    json_str = response

            # Analizar el JSON
            try:
                result = json.loads(json_str)
                return result
            except json.JSONDecodeError:
                logger.error(f"Error al decodificar JSON del LLM: {json_str}")
                # Creamos un resultado por defecto basado en heurísticas simples
                any_domain_match = any(domain.lower() in query.lower() for domain in self.domains)
                return {
                    "in_scope": any_domain_match,
                    "domain": "general business" if any_domain_match else None,
                    "confidence": 0.6,
                    "reasoning": "Fallback debido a error en respuesta LLM",
                    "explanation": "No se pudo determinar con precisión si la consulta está en el ámbito."
                }

        except Exception as e:
            logger.error(f"Error al consultar LLM para guardrail: {str(e)}")
            # Asumimos que está en el ámbito para evitar bloqueos indebidos
            return {
                "in_scope": True,
                "domain": "general business",
                "confidence": 0.5,
                "reasoning": f"Error al consultar LLM: {str(e)}",
                "explanation": "Debido a un error técnico, procesaremos tu consulta igualmente."
            }

    def _execute_impl(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Implementa la lógica del guardrail para determinar si la consulta está dentro del ámbito.
        Utiliza un LLM para evaluación inteligente en lugar de palabras clave.
        
        Args:
            input_data: Datos de entrada con la consulta y contexto
            
        Returns:
            Resultado indicando si la consulta está dentro del ámbito
        """
        start_time = time.time()

        # Obtener la consulta
        query = input_data.get("query", "").strip()
        context = input_data.get("context", {})

        # Registrar la consulta recibida
        logger.info(f"GuardrailAgent evaluando consulta: {query[:100] if len(query) > 100 else query}")

        # Validaciones básicas
        if not query:
            logger.warning("Consulta vacía proporcionada al GuardrailAgent")
            return self._create_out_of_scope_response("No has proporcionado ninguna consulta.")

        if len(query) < 3:
            logger.warning(f"Consulta demasiado corta: '{query}'")
            return self._create_out_of_scope_response("Tu consulta es demasiado corta para ser procesada.")

        # Verificar temas explícitamente excluidos
        excluded_message = self._check_explicitly_excluded(query)
        if excluded_message:
            logger.warning(f"Consulta contiene tema excluido: {query}")
            return self._create_out_of_scope_response(excluded_message)

        # Evaluar la consulta con el LLM
        evaluation = self._evaluate_with_llm(query)

        # Registrar métricas
        execution_time = time.time() - start_time
        MetricsCollector.record_agent_execution(
            agent_name="guardrail_agent",
            status=True,
            execution_time=execution_time
        )

        # Preparar respuesta según la evaluación
        if not evaluation.get("in_scope", False):
            logger.info(f"Consulta fuera del ámbito según LLM: {query}")
            return self._create_out_of_scope_response(
                specific_message=evaluation.get("explanation", None),
                reasoning=evaluation.get("reasoning", "")
            )

        # La consulta está dentro del ámbito
        domain = evaluation.get("domain", "general business")
        confidence = evaluation.get("confidence", 0.9)

        logger.info(f"Consulta dentro del ámbito del dominio '{domain}' con confianza {confidence}: {query}")

        return {
            "in_scope": True,
            "domain": domain,
            "query": query,
            "context": context,
            "confidence": confidence,
            "reasoning": evaluation.get("reasoning", "")
        }

    def _create_out_of_scope_response(self, specific_message: str | None = None, reasoning: str = "") -> dict[str, Any]:
        """
        Crea una respuesta para consultas fuera del ámbito.
        
        Args:
            specific_message: Mensaje específico para situaciones particulares
            reasoning: Razonamiento detallado sobre por qué está fuera del ámbito
            
        Returns:
            Respuesta estructurada para consultas fuera del ámbito
        """
        # Mensaje principal
        if specific_message:
            main_message = specific_message
        else:
            main_message = "Lo siento, tu consulta está fuera del ámbito de servicios que ofrecemos."

        # Lista de servicios
        services_list = "\n".join([f"- {service}" for service in self.services])

        # Mensaje completo
        message = f"{main_message}\n\nNuestros servicios están enfocados en:\n{services_list}\n\n"

        # Añadir recomendación si hay razonamiento
        if reasoning:
            recommendation = f"Sugerencia basada en el análisis: {reasoning}\n\n"
            message += recommendation

        message += "Por favor, realiza una consulta relacionada con estos servicios."

        return {
            "in_scope": False,
            "result": {
                "content": message,
                "source": "guardrail_agent",
                "type": "out_of_scope",
                "reasoning": reasoning
            },
            "confidence": 1.0
        }

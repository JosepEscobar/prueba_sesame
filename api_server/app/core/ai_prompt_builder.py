"""
Utilidades para la construcción de prompts para modelos de lenguaje.

Este módulo proporciona herramientas para crear prompts estructurados
y estandarizados para interactuar con modelos de lenguaje.
"""

import json
from typing import Any


class AIPromptBuilder:
    """
    Constructor de prompts estandarizados para interactuar con LLMs.

    Esta clase permite construir prompts estructurados de manera consistente
    para todos los agentes, facilitando la obtención de respuestas más predecibles.
    """

    def __init__(
        self,
        role: str,
        task: str,
        context: str = "",
        format_hint: str = "",
        examples: list = None,
        constraints: str = "",
        input_data: str = "",
        schema: dict[str, Any] = None,
        criteria: str = "",
    ):
        """
        Inicializa un constructor de prompts.

        Args:
            role: Rol que debe asumir el LLM (ej. "analista financiero")
            task: Tarea específica a realizar
            context: Contexto adicional para la tarea
            format_hint: Indicaciones sobre el formato esperado
            examples: Lista de ejemplos
            constraints: Restricciones o limitaciones
            input_data: Datos específicos que debe analizar el LLM
            schema: Esquema para respuestas estructuradas (para JSON)
            criteria: Criterios específicos para evaluar respuestas
        """
        self.role = role.strip()
        self.task = task.strip()
        self.context = context.strip()
        self.format_hint = format_hint.strip()
        self.examples = examples or []
        self.constraints = constraints.strip()
        self.input_data = input_data.strip()
        self.schema = schema
        self.criteria = criteria.strip()

    @staticmethod
    def create_json_extraction_prompt(
        query: str, json_structure: dict[str, Any], instructions: str = "", examples: dict[str, Any] = None
    ) -> str:
        """
        Crea un prompt estandarizado para pedir al LLM que responda en formato JSON.

        Args:
            query: La consulta o texto a analizar
            json_structure: La estructura esperada del JSON como diccionario
            instructions: Instrucciones específicas adicionales
            examples: Ejemplos opcionales para el prompt

        Returns:
            Prompt formateado
        """
        # Formatear la estructura JSON esperada como string con formato
        json_structure_str = json.dumps(json_structure, indent=2, ensure_ascii=False)

        # Base del prompt
        prompt = f"""
Analiza el siguiente texto y extrae la información en formato JSON.

Texto a analizar: "{query}"

Debes devolver ÚNICAMENTE un objeto JSON válido con la siguiente estructura:
{json_structure_str}

IMPORTANTE:
1. Responde SOLO con el JSON, sin texto adicional antes o después.
2. Asegúrate de que el JSON sea válido y tenga la estructura exacta mostrada arriba.
3. No incluyas comentarios ni explicaciones, solo el JSON.
4. Utiliza comillas dobles para las claves y valores string.
"""

        # Añadir instrucciones específicas si se proporcionan
        if instructions:
            prompt += f"\nInstrucciones adicionales:\n{instructions}\n"

        # Añadir ejemplos si se proporcionan
        if examples:
            examples_str = json.dumps(examples, indent=2, ensure_ascii=False)
            prompt += f"\nEjemplo de respuesta:\n{examples_str}\n"

        return prompt

    def build(self) -> str:
        """
        Construye y devuelve el prompt completo.

        Returns:
            El prompt formateado como string
        """
        prompt_parts = []

        if self.role:
            prompt_parts.append(f"# Rol\nActúa como {self.role}.")

        if self.task:
            prompt_parts.append(f"# Tarea\n{self.task}")

        if self.input_data:
            prompt_parts.append(f"# Datos de entrada\n{self.input_data}")

        if self.context:
            prompt_parts.append(f"# Contexto\n{self.context}")

        if self.constraints:
            prompt_parts.append(f"# Restricciones\n{self.constraints}")

        if self.criteria:
            prompt_parts.append(f"# Criterios\n{self.criteria}")

        if self.schema:
            schema_str = json.dumps(self.schema, indent=2, ensure_ascii=False)
            prompt_parts.append(
                f"# Esquema de respuesta\nDebes responder utilizando exactamente esta estructura JSON:\n```json\n{schema_str}\n```"
            )
        elif self.format_hint:
            prompt_parts.append(f"# Formato de salida esperado\n{self.format_hint}")

        if self.examples:
            examples_formatted = "\n".join(f"- {ex}" for ex in self.examples)
            prompt_parts.append(f"# Ejemplos\n{examples_formatted}")

        # Añadir instrucciones finales si hay un esquema
        if self.schema:
            prompt_parts.append(
                "# IMPORTANTE\n1. Responde SOLO con JSON válido, sin texto antes o después.\n2. Asegúrate de seguir exactamente el esquema proporcionado.\n3. Utiliza comillas dobles para las claves y valores string."
            )

        return "\n\n".join(prompt_parts)

    def build_json_prompt(self, query: str) -> str:
        """
        Construye un prompt específico para extraer JSON.

        Args:
            query: La consulta o texto a analizar

        Returns:
            El prompt formateado como string
        """
        if not self.schema:
            raise ValueError("Se requiere un esquema para construir un prompt JSON")

        # Formatear la estructura JSON esperada
        schema_str = json.dumps(self.schema, indent=2, ensure_ascii=False)

        prompt_parts = []

        if self.role:
            prompt_parts.append(f"Actúa como {self.role}.")

        # Base del prompt
        prompt_parts.append(f"Analiza el siguiente texto y extrae la información en formato JSON:\n\n{query}")

        # Formato esperado
        prompt_parts.append(
            f"Debes devolver ÚNICAMENTE un objeto JSON válido con la siguiente estructura:\n```json\n{schema_str}\n```"
        )

        # Contexto adicional
        if self.context:
            prompt_parts.append(f"Contexto adicional:\n{self.context}")

        # Criterios específicos
        if self.criteria:
            prompt_parts.append(f"Criterios:\n{self.criteria}")

        # Restricciones
        if self.constraints:
            prompt_parts.append(f"Restricciones:\n{self.constraints}")

        # Instrucciones finales
        prompt_parts.append(
            "IMPORTANTE:\n1. Responde SOLO con el JSON, sin texto adicional antes o después.\n2. Asegúrate de que el JSON sea válido y tenga la estructura exacta mostrada arriba.\n3. No incluyas comentarios ni explicaciones, solo el JSON.\n4. Utiliza comillas dobles para las claves y valores string."
        )

        # Ejemplos
        if self.examples and isinstance(self.examples[0], dict):
            # Si los ejemplos son diccionarios, asumimos que son ejemplos JSON
            example_str = json.dumps(self.examples[0], indent=2, ensure_ascii=False)
            prompt_parts.append(f"Ejemplo de respuesta:\n```json\n{example_str}\n```")

        return "\n\n".join(prompt_parts)

#!/usr/bin/env python
"""
Script para ejecutar ejemplos de uso del sistema multi-agente.
Proporciona una interfaz de línea de comandos para probar el sistema.
"""

import asyncio
import json
import argparse
import sys
import os
from typing import Dict, Any

# Añadir directorio raíz al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.orchestrator import AgentOrchestrator

# Ejemplos predefinidos
EXAMPLES = {
    "analysis": {
        "query": "Analiza este texto e identifica las principales ideas y patrones",
        "content": """
        La inteligencia artificial (IA) ha avanzado rápidamente en la última década.
        Los modelos de lenguaje de gran escala como GPT-4 pueden generar texto coherente,
        responder preguntas complejas y hasta escribir código. Sin embargo, estos sistemas
        también presentan desafíos importantes relacionados con sesgos, privacidad y control.
        Los investigadores están trabajando en mejorar estas áreas mientras las empresas
        implementan IA en diversos sectores como salud, finanzas y educación.
        """
    },
    "action": {
        "query": "Ayúdame a crear un plan de marketing digital para mi nueva tienda online",
        "action_request": "Necesito un plan paso a paso para promocionar mi tienda de ropa ecológica en redes sociales"
    },
    "summary": {
        "query": "Resume este artículo científico manteniendo los puntos más importantes",
        "content": """
        Los avances recientes en aprendizaje por refuerzo han permitido a las máquinas dominar 
        juegos complejos como el Go y el ajedrez. En este artículo, presentamos un nuevo algoritmo 
        que combina el aprendizaje por refuerzo con redes neuronales profundas para optimizar 
        la toma de decisiones en entornos con información imperfecta. Nuestros experimentos 
        demuestran que este enfoque supera significativamente los métodos anteriores en varios 
        dominios de prueba, incluidos juegos de cartas y simulaciones de estrategia militar. 
        Además, analizamos las limitaciones actuales y proponemos directrices para futuras 
        investigaciones. Los resultados sugieren que este tipo de sistemas podría tener 
        aplicaciones importantes en campos como la planificación estratégica, la logística 
        y la toma de decisiones médicas.
        """
    },
    "custom": {
        "query": "",
        "content": "",
        "action_request": ""
    }
}

async def run_example(orchestrator: AgentOrchestrator, example_type: str) -> Dict[str, Any]:
    """Ejecuta un ejemplo predefinido."""
    if example_type not in EXAMPLES:
        print(f"Ejemplo no encontrado: {example_type}")
        return None
    
    # Obtener el ejemplo
    example = EXAMPLES[example_type]
    
    if example_type == "custom":
        # Para ejemplos personalizados, solicitar entrada al usuario
        example["query"] = input("Introduce tu consulta: ")
        has_content = input("¿Quieres añadir contenido adicional? (s/n): ").lower() == "s"
        if has_content:
            example["content"] = input("Introduce el contenido: ")
        has_action = input("¿Quieres añadir una solicitud de acción? (s/n): ").lower() == "s"
        if has_action:
            example["action_request"] = input("Introduce la solicitud de acción: ")
    
    # Eliminar campos vacíos
    input_data = {k: v for k, v in example.items() if v}
    
    print("\n" + "="*50)
    print(f"Ejecutando ejemplo: {example_type}")
    print(f"Consulta: {input_data['query']}")
    if "content" in input_data:
        print(f"Contenido: {input_data['content'][:50]}...")
    if "action_request" in input_data:
        print(f"Solicitud de acción: {input_data['action_request']}")
    print("="*50 + "\n")
    
    # Procesar la solicitud
    start_message = "Procesando solicitud... (esto puede tomar un momento)"
    print(start_message)
    
    result = await orchestrator.process_request(input_data)
    
    # Borrar mensaje de inicio
    print("\r" + " " * len(start_message) + "\r", end="")
    
    return result

def display_result(result: Dict[str, Any]) -> None:
    """Muestra el resultado de manera formateada."""
    if not result:
        return
    
    print("\n" + "="*50)
    print(f"RESULTADO DEL PROCESAMIENTO")
    print("="*50)
    print(f"Estado: {result['status']}")
    print(f"Agente utilizado: {result['agent_used']}")
    print(f"Confianza: {result['confidence']:.2f}")
    print(f"Tiempo de procesamiento: {result.get('processing_time', 0):.2f} segundos")
    
    if "routing" in result:
        print("\nInformación de enrutamiento:")
        print(f"  Decisión: {result['routing']['decision']}")
        print(f"  Confianza: {result['routing']['confidence']:.2f}")
        print(f"  Razonamiento: {result['routing']['reasoning']}")
    
    print("\nRESULTADO:")
    print("-"*50)
    if result.get("result"):
        print(result["result"])
    else:
        print("No se obtuvo ningún resultado")
    
    if "error" in result:
        print("\nERROR:")
        print(result["error"])
    
    print("="*50 + "\n")

async def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(description="Ejecuta ejemplos del sistema multi-agente")
    parser.add_argument(
        "--type", "-t", 
        choices=list(EXAMPLES.keys()), 
        default="analysis",
        help="Tipo de ejemplo a ejecutar"
    )
    parser.add_argument(
        "--list", "-l", 
        action="store_true",
        help="Listar tipos de ejemplos disponibles"
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("Ejemplos disponibles:")
        for example_type in EXAMPLES:
            print(f"  - {example_type}")
        return
    
    # Crear orquestador
    orchestrator = AgentOrchestrator()
    
    # Ejecutar ejemplo
    result = await run_example(orchestrator, args.type)
    
    # Mostrar resultado
    display_result(result)

if __name__ == "__main__":
    asyncio.run(main()) 
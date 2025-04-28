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
    # Ejemplos generales
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
    
    # Ejemplos de consultoría empresarial - Marketing
    "marketing_strategy": {
        "query": "¿Qué estrategias de marketing recomiendan para lanzar un producto SaaS B2B?",
        "content": "Estamos lanzando una nueva plataforma SaaS para gestión de proyectos enfocada en empresas medianas del sector tecnológico."
    },
    "digital_marketing": {
        "query": "¿Cómo puedo mejorar el ROI de mis campañas en redes sociales?",
        "content": "Actualmente invertimos en Facebook Ads e Instagram, pero el coste por adquisición es demasiado alto."
    },
    "seo_optimization": {
        "query": "Necesito mejorar el SEO de mi sitio web de comercio electrónico",
        "content": "Vendemos productos electrónicos y no estamos apareciendo en las primeras páginas de Google para nuestras palabras clave principales."
    },
    
    # Ejemplos de consultoría empresarial - Finanzas
    "investment_strategy": {
        "query": "¿Qué estrategia de inversión recomendarías para una startup en fase seed?",
        "content": "Tenemos $500,000 en financiación inicial y necesitamos decidir cómo distribuirla para maximizar nuestro crecimiento."
    },
    "financial_analysis": {
        "query": "¿Cómo puedo mejorar el flujo de caja de mi negocio?",
        "content": "Somos una pequeña empresa manufacturera con problemas de liquidez debido a largos ciclos de pago de clientes."
    },
    "valuation": {
        "query": "¿Cómo debería valorar mi startup para una ronda de inversión Series A?",
        "content": "Tenemos dos años de operación, ingresos mensuales recurrentes de $100,000 y crecimiento del 15% mensual."
    },
    
    # Ejemplos de consultoría empresarial - Operaciones
    "supply_chain": {
        "query": "¿Cómo puedo optimizar mi cadena de suministro para reducir costos?",
        "content": "Somos una empresa de alimentos con proveedores internacionales y distribución nacional."
    },
    "process_optimization": {
        "query": "Necesito mejorar la eficiencia de nuestro proceso de atención al cliente",
        "content": "Actualmente nuestro tiempo de respuesta promedio es de 48 horas y queremos reducirlo significativamente."
    },
    "inventory_management": {
        "query": "¿Qué sistema de gestión de inventario recomiendas para una tienda minorista con múltiples ubicaciones?",
        "content": "Tenemos 5 tiendas físicas y un almacén central, con aproximadamente 2000 SKUs diferentes."
    },
    
    # Ejemplo de búsqueda de información externa
    "market_research": {
        "query": "Necesito datos actualizados sobre tendencias de consumo en comercio electrónico para 2023",
        "content": "Estoy preparando una presentación para inversores y necesito estadísticas recientes del mercado."
    },
    
    # Ejemplo personalizado
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
    
    print("\n" + "="*80)
    print(f"EJECUTANDO EJEMPLO: {example_type}")
    print("="*80)
    print(f"Consulta: {input_data['query']}")
    if "content" in input_data:
        print(f"Contenido: {input_data['content'][:100]}..." if len(input_data['content']) > 100 else f"Contenido: {input_data['content']}")
    if "action_request" in input_data:
        print(f"Solicitud de acción: {input_data['action_request']}")
    print("="*80 + "\n")
    
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
    
    print("\n" + "="*80)
    print(f"RESULTADO DEL PROCESAMIENTO")
    print("="*80)
    print(f"Estado: {result['status']}")
    print(f"Agente utilizado: {result['agent_used']}")
    print(f"Confianza: {result['confidence']:.2f}")
    print(f"Tiempo de procesamiento: {result.get('processing_time', 0):.2f} segundos")
    
    if "routing" in result:
        print("\nInformación de enrutamiento:")
        print(f"  Decisión: {result['routing']['decision']}")
        print(f"  Confianza: {result['routing']['confidence']:.2f}")
        print(f"  Razonamiento: {result['routing']['reasoning']}")
    
    # Mostrar información adicional si existe
    if "additional_info" in result and "data_lookup" in result["additional_info"]:
        print("\nInformación adicional de búsqueda de datos:")
        print(f"  Tiempo de ejecución: {result['additional_info']['data_lookup']['execution_time']:.2f} segundos")
        print(f"  Confianza: {result['additional_info']['data_lookup']['confidence']:.2f}")
    
    print("\nRESULTADO:")
    print("-"*80)
    if result.get("result"):
        print(result["result"])
    else:
        print("No se obtuvo ningún resultado")
    
    if "error" in result:
        print("\nERROR:")
        print(result["error"])
    
    print("="*80 + "\n")

def list_examples_by_category():
    """Muestra los ejemplos disponibles organizados por categoría."""
    categories = {
        "General": ["analysis", "action", "summary"],
        "Marketing": ["marketing_strategy", "digital_marketing", "seo_optimization"],
        "Finanzas": ["investment_strategy", "financial_analysis", "valuation"],
        "Operaciones": ["supply_chain", "process_optimization", "inventory_management"],
        "Búsqueda de Datos": ["market_research"],
        "Otros": ["custom"]
    }
    
    print("\nEjemplos disponibles por categoría:")
    for category, examples in categories.items():
        print(f"\n{category}:")
        for example in examples:
            print(f"  - {example}: {EXAMPLES[example]['query'][:70]}...")

async def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(description="Ejecuta ejemplos del sistema multi-agente")
    parser.add_argument(
        "--type", "-t", 
        choices=list(EXAMPLES.keys()), 
        default="marketing_strategy",
        help="Tipo de ejemplo a ejecutar"
    )
    parser.add_argument(
        "--list", "-l", 
        action="store_true",
        help="Listar tipos de ejemplos disponibles"
    )
    parser.add_argument(
        "--category", "-c", 
        action="store_true",
        help="Listar ejemplos por categoría"
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("Ejemplos disponibles:")
        for example_type in EXAMPLES:
            print(f"  - {example_type}: {EXAMPLES[example_type]['query'][:70]}...")
        return
        
    if args.category:
        list_examples_by_category()
        return
    
    # Crear orquestador
    orchestrator = AgentOrchestrator()
    
    # Ejecutar ejemplo
    result = await run_example(orchestrator, args.type)
    
    # Mostrar resultado
    display_result(result)

if __name__ == "__main__":
    asyncio.run(main()) 
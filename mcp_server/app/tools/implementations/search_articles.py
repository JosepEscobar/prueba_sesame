"""
Implementación de herramientas para búsqueda de artículos.

Este módulo contiene herramientas para buscar artículos y
contenido relacionado con diversos temas utilizando APIs externas.
"""

import logging
import re
from datetime import datetime
from typing import Any

import httpx

# Configurar logging
logger = logging.getLogger("app")


async def search_articles(
    tema: str | None = None,
    query: str | None = None,
    max_resultados: int = 5,
    incluir_resumen: bool = True,
    fuentes: list[str] | None = None,
) -> dict[str, Any]:
    """
    Busca artículos y noticias relacionados con un tema específico mediante APIs públicas.

    Args:
        tema: Tema o palabra clave para buscar (alternativa a query)
        query: Tema o palabra clave para buscar (alternativa a tema)
        max_resultados: Número máximo de resultados a devolver
        incluir_resumen: Si se debe incluir un resumen de cada artículo
        fuentes: Lista de fuentes específicas donde buscar (opcional)

    Returns:
        Lista de artículos encontrados con metadatos
    """
    # Usar tema o query, dando prioridad a tema si ambos están presentes
    tema_busqueda = tema if tema is not None else query

    if tema_busqueda is None:
        return {"error": "Debe proporcionar un parámetro 'tema' o 'query' para la búsqueda"}

    # Limitar el número máximo de resultados
    if max_resultados > 10:
        max_resultados = 10

    # Configuración del servicio de búsqueda (Wikipedia API como ejemplo)
    try:
        # Usar Wikipedia API como fuente de artículos
        logger.info(f"Realizando búsqueda de artículos para: {tema_busqueda}")

        # Construir URL para API de Wikipedia
        base_url = "https://es.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": tema_busqueda,
            "utf8": 1,
            "srlimit": max_resultados,
        }

        # Usar httpx para peticiones asíncronas
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params)

            if response.status_code != 200:
                logger.error(f"Error en la API de Wikipedia: {response.status_code}")
                return {"error": f"Error al consultar la API externa: {response.status_code}"}

            # Procesar los resultados
            resultados_api = response.json()
            articulos = []

            if "query" in resultados_api and "search" in resultados_api["query"]:
                for item in resultados_api["query"]["search"]:
                    # Crear URL para el artículo
                    titulo_url = item["title"].replace(" ", "_")
                    url = f"https://es.wikipedia.org/wiki/{titulo_url}"

                    articulo = {
                        "titulo": item["title"],
                        "fuente": "Wikipedia",
                        "fecha": datetime.now().strftime("%Y-%m-%d"),  # Wikipedia no proporciona fecha en esta API
                        "url": url,
                    }

                    # Añadir resumen si se solicita
                    if incluir_resumen:
                        # El snippet ya viene en el resultado, pero puede tener marcado HTML
                        resumen = re.sub(r"<.*?>", "", item["snippet"])
                        articulo["resumen"] = resumen

                    articulos.append(articulo)

            # Filtrar por fuentes si se especifica
            if fuentes and "Wikipedia" not in [f.lower() for f in fuentes]:
                # Si se piden fuentes específicas y Wikipedia no está entre ellas
                # En un caso real, aquí se harían llamadas a otras APIs para esas fuentes
                logger.warning(f"Fuentes solicitadas no disponibles: {fuentes}")
                # No devolvemos error, sino un conjunto vacío de resultados
                articulos = []

            return {
                "tema": tema_busqueda,
                "num_resultados": len(articulos),
                "fecha_busqueda": datetime.now().strftime("%Y-%m-%d"),
                "articulos": articulos,
            }

    except Exception as e:
        logger.error(f"Error al buscar artículos: {str(e)}")
        return {
            "error": f"Error interno al buscar artículos: {str(e)}",
            "tema": tema_busqueda,
            "num_resultados": 0,
            "articulos": [],
        }

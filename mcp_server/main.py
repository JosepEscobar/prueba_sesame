#!/usr/bin/env python3
"""
Servidor MCP (Model Context Protocol) para Sesame.

Este servidor expone herramientas financieras, de análisis y de marketing
a través del protocolo MCP estándar para que puedan ser utilizadas por
modelos como Claude, GPT y otros agentes compatibles con MCP.

Soporta dos modos de operación:
1. HTTP/SSE: Para conexiones estándar a través de la red
2. Stdio: Para comunicación directa a través de entrada/salida estándar
"""

import logging
import os
import socket
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

# Importar FastAPI
import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, Request

# Importar implementaciones desde módulos correspondientes
from app.tools.implementations import AVAILABLE_TOOLS

# Configurar logging
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "logs" / "app.log"),
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger("mcp_server")

# Crear la aplicación FastAPI
app = FastAPI(
    title="Sesame MCP Server",
    description="Servidor MCP para herramientas financieras, análisis y marketing",
    version="1.0.0",
)


# Middleware para registrar todas las solicitudes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Registrar solicitud entrante
    logger.info(f"Solicitud recibida: {request.method} {request.url.path}")

    # Obtener el cuerpo de la solicitud si es POST o PUT
    if request.method in ("POST", "PUT"):
        try:
            # Crear una copia del cuerpo para no interferir con el procesamiento principal
            body = await request.body()
            # No intentamos hacer seek en el objeto bytes
            if body:
                # Limitar el tamaño del cuerpo en los logs
                body_str = body.decode("utf-8", errors="replace")
                if len(body_str) > 500:
                    body_str = body_str[:500] + "... [truncado]"
                logger.info(f"Cuerpo de la solicitud: {body_str}")
        except Exception as e:
            logger.warning(f"No se pudo leer el cuerpo de la solicitud: {str(e)}")

    # Continuar con la solicitud
    response = await call_next(request)
    logger.info(f"Respuesta: {response.status_code}")

    return response


# Crear router para la API MCP
mcp_router = APIRouter(prefix="/mcp/v1")

# Registro de herramientas
tools_registry = {}


def register_tool(name: str = None):
    """
    Decorador para registrar una herramienta en el servidor MCP.
    """

    def decorator(func: Callable):
        nonlocal name
        tool_name = name or func.__name__
        tools_registry[tool_name] = func
        return func

    return decorator


# Endpoint raíz
@app.get("/")
async def root():
    return {"message": "Servidor MCP de Sesame Tools", "version": "1.0.0"}


# Listar todas las herramientas disponibles
@mcp_router.get("/tools")
async def list_tools():
    """Listar todas las herramientas disponibles."""
    tools = []
    for name, tool_func in tools_registry.items():
        tools.append(
            {
                "name": name,
                "description": tool_func.__doc__ or "",
            }
        )
    return {"tools": tools}


# Ejecutar una herramienta
@mcp_router.post("/tools/{tool_name}")
async def execute_tool(tool_name: str, request: Request):
    """Ejecutar una herramienta específica."""
    if tool_name not in tools_registry:
        raise HTTPException(
            status_code=404, detail=f"Herramienta '{tool_name}' no encontrada"
        )

    try:
        # Obtener parámetros de la solicitud
        params = await request.json()

        # Ejecutar la herramienta
        tool_func = tools_registry[tool_name]
        result = await tool_func(**params)

        # Devolver el resultado
        return {"result": result}
    except Exception as e:
        logger.error(f"Error al ejecutar herramienta {tool_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en la ejecución: {str(e)}")


# ---- Herramientas de análisis financiero ----


@register_tool()
async def buscar_datos_financieros(
    empresa: str, periodo: str | None = None
) -> dict[str, Any]:
    """
    Busca datos financieros de una empresa específica.

    Args:
        empresa: Nombre o ticker de la empresa
        periodo: Periodo para los datos (trimestre/año). Si no se especifica, se usa el último disponible.

    Returns:
        Datos financieros de la empresa
    """
    # En una implementación real, esto conectaría con una API o base de datos financiera
    hoy = datetime.now().strftime("%Y-%m-%d")
    periodo_actual = periodo or f"Q1 {datetime.now().year}"

    return {
        "empresa": empresa,
        "periodo": periodo_actual,
        "fecha_consulta": hoy,
        "datos": {
            "ingresos": 1250000,
            "beneficio_neto": 450000,
            "activos_totales": 5600000,
            "pasivos_totales": 2300000,
            "flujo_caja": 380000,
            "margen_beneficio": 0.36,
            "ROI": 0.22,
        },
    }


@register_tool()
async def calcular_ratios_financieros(
    ingresos: float,
    beneficio_neto: float,
    activos_totales: float,
    pasivos_totales: float,
) -> dict[str, float]:
    """
    Calcula ratios financieros a partir de datos básicos.

    Args:
        ingresos: Ingresos totales del periodo
        beneficio_neto: Beneficio neto del periodo
        activos_totales: Valor de los activos totales
        pasivos_totales: Valor de los pasivos totales

    Returns:
        Ratios financieros calculados
    """
    patrimonio_neto = activos_totales - pasivos_totales

    # Evitar divisiones por cero
    if ingresos == 0:
        margen_beneficio = 0
    else:
        margen_beneficio = beneficio_neto / ingresos

    if activos_totales == 0:
        roa = 0
    else:
        roa = beneficio_neto / activos_totales

    if patrimonio_neto == 0:
        roe = 0
    else:
        roe = beneficio_neto / patrimonio_neto

    if pasivos_totales == 0:
        ratio_endeudamiento = 0
    else:
        ratio_endeudamiento = pasivos_totales / activos_totales

    return {
        "margen_beneficio": margen_beneficio,
        "ROA": roa,
        "ROE": roe,
        "ratio_endeudamiento": ratio_endeudamiento,
        "ratio_liquidez": activos_totales
        / (pasivos_totales if pasivos_totales > 0 else 1),
    }


# ---- Herramientas de análisis de marketing ----


@register_tool()
async def analizar_rendimiento_campania(
    nombre_campania: str, impresiones: int, clics: int, conversiones: int, coste: float
) -> dict[str, Any]:
    """
    Analiza el rendimiento de una campaña de marketing.

    Args:
        nombre_campania: Nombre de la campaña
        impresiones: Número total de impresiones
        clics: Número total de clics
        conversiones: Número total de conversiones
        coste: Coste total de la campaña

    Returns:
        Análisis de rendimiento de la campaña
    """
    # Cálculo de métricas básicas
    ctr = clics / impresiones if impresiones > 0 else 0
    cpc = coste / clics if clics > 0 else 0
    conversion_rate = conversiones / clics if clics > 0 else 0
    cpa = coste / conversiones if conversiones > 0 else 0
    roi = (conversiones * 100 - coste) / coste if coste > 0 else 0

    return {
        "campania": nombre_campania,
        "metricas": {
            "CTR": ctr,
            "CPC": cpc,
            "tasa_conversion": conversion_rate,
            "CPA": cpa,
            "ROI": roi,
        },
        "evaluacion": {
            "rendimiento_ctr": "Bueno"
            if ctr > 0.02
            else "Regular"
            if ctr > 0.01
            else "Bajo",
            "eficiencia_coste": "Buena"
            if cpa < 50
            else "Regular"
            if cpa < 100
            else "Baja",
            "rentabilidad": "Alta" if roi > 1 else "Media" if roi > 0 else "Baja",
        },
    }


@register_tool()
async def recomendar_estrategia_marketing(
    industria: str,
    presupuesto: float,
    objetivo: str,
    publico_objetivo: str | None = None,
) -> dict[str, Any]:
    """
    Recomienda una estrategia de marketing basada en parámetros básicos.

    Args:
        industria: Industria o sector del negocio
        presupuesto: Presupuesto disponible
        objetivo: Objetivo principal (awareness, conversiones, fidelización)
        publico_objetivo: Descripción del público objetivo

    Returns:
        Recomendación de estrategia de marketing
    """
    # En una implementación real, esto podría usar un modelo ML o reglas más complejas
    # Este es un ejemplo simplificado

    estrategias = {
        "awareness": [
            "Campañas de display en redes sociales",
            "Marketing de contenidos",
            "Relaciones públicas",
        ],
        "conversiones": [
            "Publicidad en buscadores (SEM)",
            "Email marketing",
            "Retargeting",
        ],
        "fidelización": [
            "Programas de lealtad",
            "Email marketing personalizado",
            "Comunidad en redes sociales",
        ],
    }

    objetivo_norm = objetivo.lower()
    if objetivo_norm not in estrategias:
        objetivo_norm = "conversiones"  # Valor por defecto

    # Seleccionar canales según presupuesto
    canales = []
    if presupuesto < 10000:
        canales = estrategias[objetivo_norm][:1]  # Pocos canales para presupuesto bajo
    elif presupuesto < 50000:
        canales = estrategias[objetivo_norm][:2]  # Canales moderados
    else:
        canales = estrategias[objetivo_norm]  # Todos los canales

    # Distribuir presupuesto
    presupuesto_por_canal = {}
    num_canales = len(canales)
    for i, canal in enumerate(canales):
        if i == num_canales - 1:
            # El último canal recibe el resto
            porcentaje = 100 - sum(presupuesto_por_canal.values())
        else:
            # Los demás se reparten equitativamente
            porcentaje = 100 // num_canales
        presupuesto_por_canal[canal] = porcentaje

    return {
        "estrategia": f"Estrategia de {objetivo_norm} para {industria}",
        "canales_recomendados": canales,
        "distribucion_presupuesto": presupuesto_por_canal,
        "presupuesto_total": presupuesto,
        "publico_objetivo": publico_objetivo,
    }


@register_tool()
async def analizar_tendencia(
    datos: list[float], etiquetas: list[str] | None = None
) -> dict[str, Any]:
    """
    Analiza la tendencia en una serie de datos.

    Args:
        datos: Lista de valores numéricos
        etiquetas: Etiquetas para cada valor (opcional)

    Returns:
        Análisis de la tendencia
    """
    if not datos or len(datos) < 2:
        return {"error": "Se necesitan al menos dos puntos de datos"}

    # Crear etiquetas si no se proporcionaron
    if not etiquetas:
        etiquetas = [f"Punto {i + 1}" for i in range(len(datos))]
    elif len(etiquetas) < len(datos):
        # Completar etiquetas faltantes
        etiquetas.extend([f"Punto {i + 1}" for i in range(len(etiquetas), len(datos))])

    # Calcular cambio total
    cambio_total = datos[-1] - datos[0]
    cambio_porcentual = (
        (cambio_total / datos[0]) * 100 if datos[0] != 0 else float("inf")
    )

    # Determinar dirección de la tendencia
    if cambio_total > 0:
        direccion = "creciente"
    elif cambio_total < 0:
        direccion = "decreciente"
    else:
        direccion = "estable"

    # Calcular volatilidad (desviación estándar)
    media = sum(datos) / len(datos)
    varianza = sum((x - media) ** 2 for x in datos) / len(datos)
    volatilidad = varianza**0.5

    return {
        "tendencia": {
            "direccion": direccion,
            "cambio_total": cambio_total,
            "cambio_porcentual": cambio_porcentual,
        },
        "datos": {
            "valores": datos,
            "etiquetas": etiquetas,
            "media": media,
            "volatilidad": volatilidad,
        },
        "analisis": f"La tendencia es {direccion} con un cambio total de {cambio_total:.2f} ({cambio_porcentual:.2f}%)",
    }


@register_tool()
async def predecir_valores(
    datos: list[float], periodos_futuros: int = 3
) -> dict[str, Any]:
    """
    Predice valores futuros basados en datos históricos.

    Args:
        datos: Serie histórica de valores
        periodos_futuros: Número de periodos a predecir

    Returns:
        Predicciones de valores futuros
    """
    if not datos or len(datos) < 3:
        return {
            "error": "Se necesitan al menos tres puntos de datos para hacer predicciones"
        }

    if periodos_futuros < 1:
        return {"error": "El número de periodos a predecir debe ser al menos 1"}

    # Implementación simple: usamos la tendencia lineal
    x = list(range(len(datos)))
    y = datos

    # Calcular pendiente (m) y ordenada (b) de la recta y = mx + b
    n = len(datos)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y, strict=False))
    sum_x2 = sum(xi**2 for xi in x)

    # Fórmulas de regresión lineal
    try:
        m = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
        b = (sum_y - m * sum_x) / n

        # Predecir los siguientes periodos
        predicciones = [m * (len(datos) + i) + b for i in range(periodos_futuros)]

        # Calcular R^2 (coeficiente de determinación)
        y_pred = [m * xi + b for xi in x]
        ss_res = sum((yi - pred) ** 2 for yi, pred in zip(y, y_pred, strict=False))
        ss_tot = sum((yi - sum_y / n) ** 2 for yi in y)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        confianza = "alta" if r2 > 0.7 else "media" if r2 > 0.4 else "baja"

        return {
            "predicciones": predicciones,
            "metodo": "regresión lineal",
            "metricas": {
                "pendiente": m,
                "intercepto": b,
                "r_cuadrado": r2,
                "confianza": confianza,
            },
        }
    except Exception as e:
        return {"error": f"Error al calcular predicciones: {str(e)}"}


@register_tool()
async def financial_models(
    industria: str, metodo: str, datos: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Proporciona modelos financieros y análisis para una industria específica.

    Args:
        industria: Industria o sector para analizar
        metodo: Tipo de análisis financiero a realizar
        datos: Datos adicionales para el análisis (opcional)

    Returns:
        Resultados del análisis financiero
    """
    # Datos de ejemplo para diferentes industrias
    modelos_industria = {
        "tecnología": {
            "crecimiento_anual": 14.5,
            "margen_beneficio_promedio": 22.3,
            "inversion_id_promedio": 18.2,
            "roi_esperado": 25.4,
            "tiempo_recuperacion": 2.5,
        },
        "finanzas": {
            "crecimiento_anual": 8.2,
            "margen_beneficio_promedio": 30.1,
            "inversion_id_promedio": 5.3,
            "roi_esperado": 18.7,
            "tiempo_recuperacion": 3.8,
        },
        "salud": {
            "crecimiento_anual": 7.5,
            "margen_beneficio_promedio": 15.8,
            "inversion_id_promedio": 12.4,
            "roi_esperado": 16.5,
            "tiempo_recuperacion": 4.2,
        },
        "retail": {
            "crecimiento_anual": 4.8,
            "margen_beneficio_promedio": 8.2,
            "inversion_id_promedio": 3.1,
            "roi_esperado": 12.3,
            "tiempo_recuperacion": 3.1,
        },
    }

    # Si la industria no está en nuestros datos, usar tecnología como default
    industria_data = modelos_industria.get(
        industria.lower(), modelos_industria["tecnología"]
    )

    # Procesar según el método solicitado
    if metodo == "proyeccion_crecimiento":
        # Proyección de crecimiento para los próximos 5 años
        crecimiento_base = industria_data["crecimiento_anual"]
        proyeccion = [round(crecimiento_base * (1 + 0.05 * i), 2) for i in range(5)]
        return {
            "industria": industria,
            "metodo": metodo,
            "proyeccion_5_años": proyeccion,
            "crecimiento_promedio": sum(proyeccion) / len(proyeccion),
        }

    elif metodo == "analisis_rentabilidad":
        # Análisis de rentabilidad
        return {
            "industria": industria,
            "metodo": metodo,
            "margen_beneficio": industria_data["margen_beneficio_promedio"],
            "roi": industria_data["roi_esperado"],
            "tiempo_recuperacion_años": industria_data["tiempo_recuperacion"],
        }

    elif metodo == "comparativa_industria":
        # Comparativa con otras industrias
        comparativa = {}
        for ind, data in modelos_industria.items():
            comparativa[ind] = {
                "crecimiento": data["crecimiento_anual"],
                "margen": data["margen_beneficio_promedio"],
            }
        return {
            "industria_base": industria,
            "metodo": metodo,
            "comparativa": comparativa,
        }

    else:
        # Método no reconocido, devolver datos generales
        return {
            "industria": industria,
            "datos_financieros": industria_data,
            "nota": "Método no reconocido, se devuelven datos generales de la industria",
        }


# -- Registrar todas las herramientas automáticamente desde AVAILABLE_TOOLS --
for tool_func in AVAILABLE_TOOLS:
    tool_name = tool_func.__name__
    logger.info(f"Registrando herramienta: {tool_name}")
    register_tool(name=tool_name)(tool_func)


# Status endpoint
@app.get("/status")
async def status():
    """Retorna el estado actual del servidor MCP."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "tools_count": len(tools_registry),
        "tools": list(tools_registry.keys()),
    }


# Incluir el router en la aplicación
app.include_router(mcp_router)


# Añadir endpoints compatibles en la ruta raíz
@app.get("/tools")
async def list_tools_root():
    """Listar todas las herramientas disponibles (endpoint compatible)."""
    return await list_tools()


@app.post("/tools/{tool_name}")
async def execute_tool_root(tool_name: str, request: Request):
    """Ejecutar una herramienta específica (endpoint compatible)."""
    return await execute_tool(tool_name, request)


# Función de inicio del servidor
def iniciar_servidor():
    """Inicia el servidor MCP."""
    # Verificar puerto disponible
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "4000"))

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.close()
    except OSError:
        # Puerto en uso, ajustar
        port += 1
        os.environ["MCP_PORT"] = str(port)
        logger.info(f"Puerto {port - 1} en uso, usando puerto alternativo: {port}")

    # Iniciar el servidor
    logger.info(f"Iniciando servidor MCP en {host}:{port}")

    # Añadir un log para mostrar las herramientas registradas
    logger.info(f"Herramientas registradas: {list(tools_registry.keys())}")

    # Iniciar uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    iniciar_servidor()

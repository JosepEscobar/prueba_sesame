"""
Implementaciones de herramientas para modelos financieros.

Este módulo contiene herramientas para realizar diversos análisis financieros,
calcular ratios, recomendar estrategias y realizar predicciones.
"""

import math
import random
from datetime import datetime
from typing import Any


async def calcular_ratios_financieros(
    ingresos: float, beneficio_neto: float, activos_totales: float, pasivos_totales: float
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

    ratios = {
        "margen_beneficio": round(margen_beneficio, 4),
        "ROA": round(roa, 4),
        "ROE": round(roe, 4),
        "ratio_endeudamiento": round(ratio_endeudamiento, 4),
        "ratio_liquidez": round(activos_totales / (pasivos_totales if pasivos_totales > 0 else 1), 4),
        "patrimonio_neto": patrimonio_neto,
    }

    # Añadir interpretaciones
    interpretaciones = {
        "margen_beneficio": interpretar_margen(margen_beneficio),
        "ROA": interpretar_roa(roa),
        "ROE": interpretar_roe(roe),
        "ratio_endeudamiento": interpretar_endeudamiento(ratio_endeudamiento),
        "ratio_liquidez": interpretar_liquidez(ratios["ratio_liquidez"]),
    }

    return {
        "ratios": ratios,
        "interpretaciones": interpretaciones,
        "recomendaciones": generar_recomendaciones_ratios(ratios),
        "fecha_calculo": datetime.now().strftime("%Y-%m-%d"),
    }


def interpretar_margen(valor: float) -> str:
    """Interpreta el valor del margen de beneficio."""
    if valor < 0:
        return "Crítico: La empresa está operando con pérdidas."
    elif valor < 0.05:
        return "Bajo: Margen de beneficio muy reducido, típico de sectores con alta competencia."
    elif valor < 0.10:
        return "Moderado: Margen de beneficio aceptable pero con espacio para mejora."
    elif valor < 0.20:
        return "Bueno: Margen de beneficio saludable, indica buena gestión operativa."
    else:
        return "Excelente: Margen de beneficio muy alto, típico de empresas con ventajas competitivas."


def interpretar_roa(valor: float) -> str:
    """Interpreta el valor del ROA (Return on Assets)."""
    if valor < 0:
        return "Crítico: Los activos no están generando retorno positivo."
    elif valor < 0.02:
        return "Bajo: Rendimiento de activos pobre, posible uso ineficiente de recursos."
    elif valor < 0.05:
        return "Moderado: Rendimiento de activos aceptable pero mejorable."
    elif valor < 0.10:
        return "Bueno: Buen rendimiento de activos, indica eficiencia operativa."
    else:
        return "Excelente: Rendimiento de activos excepcional, empresa muy eficiente."


def interpretar_roe(valor: float) -> str:
    """Interpreta el valor del ROE (Return on Equity)."""
    if valor < 0:
        return "Crítico: La inversión de los accionistas está perdiendo valor."
    elif valor < 0.05:
        return "Bajo: Rendimiento de la inversión pobre para los accionistas."
    elif valor < 0.10:
        return "Moderado: Rendimiento aceptable pero por debajo de lo óptimo."
    elif valor < 0.20:
        return "Bueno: Buen rendimiento para los accionistas."
    else:
        return "Excelente: Rendimiento excepcional para los accionistas."


def interpretar_endeudamiento(valor: float) -> str:
    """Interpreta el ratio de endeudamiento."""
    if valor > 0.8:
        return "Crítico: Nivel de endeudamiento muy alto, riesgo significativo."
    elif valor > 0.6:
        return "Alto: Endeudamiento elevado, podría limitar opciones de financiación."
    elif valor > 0.4:
        return "Moderado: Endeudamiento equilibrado."
    elif valor > 0.2:
        return "Bajo: Endeudamiento reducido, indica solidez financiera."
    else:
        return "Muy bajo: Endeudamiento mínimo, gran seguridad financiera."


def interpretar_liquidez(valor: float) -> str:
    """Interpreta el ratio de liquidez."""
    if valor < 1:
        return "Crítico: Problemas potenciales para cubrir obligaciones a corto plazo."
    elif valor < 1.5:
        return "Justo: Liquidez limitada pero suficiente."
    elif valor < 2:
        return "Bueno: Buena capacidad para cubrir obligaciones a corto plazo."
    elif valor < 3:
        return "Muy bueno: Sólida posición de liquidez."
    else:
        return "Excelente: Liquidez abundante, podría considerar reinversión."


def generar_recomendaciones_ratios(ratios: dict[str, float]) -> list[str]:
    """Genera recomendaciones basadas en los ratios calculados."""
    recomendaciones = []

    # Recomendaciones para el margen de beneficio
    if ratios["margen_beneficio"] < 0.05:
        recomendaciones.append(
            "Considerar estrategias para aumentar el margen: revisar precios, reducir costos operativos o enfocarse en productos/servicios más rentables."
        )

    # Recomendaciones para ROA
    if ratios["ROA"] < 0.03:
        recomendaciones.append(
            "Mejorar la utilización de activos: considerar la venta de activos improductivos o aumentar la eficiencia operativa."
        )

    # Recomendaciones para el endeudamiento
    if ratios["ratio_endeudamiento"] > 0.7:
        recomendaciones.append(
            "Reducir nivel de deuda: desarrollar un plan para reducir pasivos y fortalecer la posición financiera."
        )
    elif ratios["ratio_endeudamiento"] < 0.2 and ratios["ROE"] < 0.15:
        recomendaciones.append(
            "Considerar opciones de apalancamiento financiero para potenciar el rendimiento para los accionistas."
        )

    # Recomendaciones para liquidez
    if ratios["ratio_liquidez"] > 3:
        recomendaciones.append("Exceso de liquidez: considerar reinversión en el negocio o distribución a accionistas.")
    elif ratios["ratio_liquidez"] < 1.2:
        recomendaciones.append("Fortalecer la posición de liquidez para asegurar la capacidad de pago a corto plazo.")

    # Si no hay recomendaciones específicas
    if not recomendaciones:
        recomendaciones.append(
            "Los indicadores financieros muestran una posición equilibrada. Mantener estrategia actual y monitorear periódicamente."
        )

    return recomendaciones


async def recomendar_estrategia_marketing(
    industria: str, presupuesto: float, objetivo: str, publico_objetivo: str | None = None
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
    estrategias = {
        "awareness": [
            "Campañas de display en redes sociales",
            "Marketing de contenidos",
            "Relaciones públicas",
            "Publicidad en YouTube",
            "Colaboraciones con influencers",
        ],
        "conversiones": [
            "Publicidad en buscadores (SEM)",
            "Email marketing",
            "Retargeting",
            "Landing pages optimizadas",
            "Campañas promocionales",
        ],
        "fidelización": [
            "Programas de lealtad",
            "Email marketing personalizado",
            "Comunidad en redes sociales",
            "Servicio al cliente premium",
            "Contenido exclusivo para clientes",
        ],
    }

    # Normalizar objetivo
    objetivo_norm = objetivo.lower()
    if objetivo_norm not in estrategias:
        objetivo_norm = "conversiones"  # Valor por defecto

    # Determinar canales según presupuesto
    canales = []
    if presupuesto < 10000:
        canales = estrategias[objetivo_norm][:2]  # Pocos canales para presupuesto bajo
        nivel_presupuesto = "bajo"
    elif presupuesto < 50000:
        canales = estrategias[objetivo_norm][:3]  # Canales moderados
        nivel_presupuesto = "medio"
    else:
        canales = estrategias[objetivo_norm]  # Todos los canales
        nivel_presupuesto = "alto"

    # Distribución del presupuesto
    distribucion = {}
    if len(canales) > 0:
        # Asignar porcentajes de forma aleatoria pero que sumen 100%
        porcentajes = [random.randint(1, 100) for _ in range(len(canales))]
        total = sum(porcentajes)
        porcentajes = [round((p / total) * 100) for p in porcentajes]

        # Ajustar para asegurar que sumen exactamente 100%
        porcentajes[-1] = 100 - sum(porcentajes[:-1])

        for i, canal in enumerate(canales):
            distribucion[canal] = porcentajes[i]

    # Adaptar según industria
    adaptaciones_industria = {}
    industrias_conocidas = ["tecnología", "salud", "finanzas", "retail", "manufactura", "educación", "entretenimiento"]

    if any(ind in industria.lower() for ind in industrias_conocidas):
        # Recomendaciones específicas por industria
        if "tecnología" in industria.lower():
            adaptaciones_industria = {
                "canales_adicionales": ["Marketing en LinkedIn", "Content marketing técnico"],
                "enfoque": "Destacar innovación y soluciones técnicas",
            }
        elif "salud" in industria.lower():
            adaptaciones_industria = {
                "canales_adicionales": ["Webinars educativos", "Publicaciones científicas"],
                "enfoque": "Comunicar confianza, seguridad y evidencia científica",
            }
        elif "finanzas" in industria.lower():
            adaptaciones_industria = {
                "canales_adicionales": ["Seminarios de educación financiera", "Newsletters especializadas"],
                "enfoque": "Transmitir seguridad, confianza y transparencia",
            }

    # Construir el resultado
    resultado = {
        "industria": industria,
        "objetivo": objetivo,
        "nivel_presupuesto": nivel_presupuesto,
        "presupuesto_total": presupuesto,
        "canales_recomendados": canales,
        "distribucion_presupuesto": distribucion,
        "calendario_sugerido": generar_calendario_marketing(),
        "fecha_recomendacion": datetime.now().strftime("%Y-%m-%d"),
    }

    # Añadir adaptaciones por industria si existen
    if adaptaciones_industria:
        resultado["adaptaciones_industria"] = adaptaciones_industria

    # Añadir segmentación si se proporciona público objetivo
    if publico_objetivo:
        resultado["segmentacion"] = {
            "publico_objetivo": publico_objetivo,
            "recomendaciones_segmentacion": [
                "Personalizar mensajes según características del público",
                "Adaptar canales según hábitos de consumo del segmento",
                "Realizar pruebas A/B para optimizar la comunicación",
            ],
        }

    return resultado


def generar_calendario_marketing() -> dict[str, list[str]]:
    """Genera un calendario sugerido para implementar la estrategia de marketing."""
    meses = ["Mes 1", "Mes 2", "Mes 3"]
    calendario = {}

    for mes in meses:
        calendario[mes] = [
            f"Semana 1: {random.choice(['Preparación', 'Análisis', 'Planificación'])}",
            f"Semana 2: {random.choice(['Implementación', 'Lanzamiento', 'Optimización'])}",
            f"Semana 3: {random.choice(['Monitorización', 'Ajustes', 'Evaluación'])}",
            f"Semana 4: {random.choice(['Análisis de resultados', 'Reporte', 'Planificación siguiente fase'])}",
        ]

    return calendario


async def analizar_tendencia(datos: list[float], etiquetas: list[str] | None = None) -> dict[str, Any]:
    """
    Analiza la tendencia en una serie de datos.

    Args:
        datos: Lista de valores numéricos
        etiquetas: Opcional. Etiquetas para cada punto de datos (ej. fechas)

    Returns:
        Análisis de tendencia con métricas y visualización
    """
    if len(datos) < 2:
        return {"error": "Se necesitan al menos dos puntos de datos para analizar tendencia", "success": False}

    # Crear etiquetas por defecto si no se proporcionan
    if not etiquetas:
        etiquetas = [f"Punto {i + 1}" for i in range(len(datos))]
    elif len(etiquetas) != len(datos):
        # Ajustar si hay discrepancia
        if len(etiquetas) < len(datos):
            etiquetas.extend([f"Punto {i + 1 + len(etiquetas)}" for i in range(len(datos) - len(etiquetas))])
        else:
            etiquetas = etiquetas[: len(datos)]

    # Calcular estadísticas básicas
    promedio = sum(datos) / len(datos)
    maximo = max(datos)
    minimo = min(datos)
    rango = maximo - minimo

    # Calcular tendencia (pendiente)
    x = list(range(len(datos)))
    n = len(datos)

    # Calcular pendiente usando mínimos cuadrados
    numerador = n * sum(x_i * y_i for x_i, y_i in zip(x, datos, strict=False)) - sum(x) * sum(datos)
    denominador = n * sum(x_i**2 for x_i in x) - sum(x) ** 2

    if denominador == 0:  # Evitar división por cero
        pendiente = 0
    else:
        pendiente = numerador / denominador

    # Determinar dirección de tendencia
    if pendiente > 0.01:
        direccion = "creciente"
    elif pendiente < -0.01:
        direccion = "decreciente"
    else:
        direccion = "estable"

    # Calcular volatilidad (desviación estándar)
    if len(datos) < 2:
        volatilidad = 0
    else:
        varianza = sum((x - promedio) ** 2 for x in datos) / (len(datos) - 1)
        volatilidad = math.sqrt(varianza)

    # Calcular cambio porcentual
    if datos[0] != 0:
        cambio_porcentual = ((datos[-1] - datos[0]) / abs(datos[0])) * 100
    else:
        cambio_porcentual = 0

    # Calcular datos de autocorrelación para detectar estacionalidad
    tiene_estacionalidad = False
    if len(datos) >= 4:
        # Correlación simplificada con lag=1 y lag=2
        lag1 = sum((datos[i] - promedio) * (datos[i - 1] - promedio) for i in range(1, len(datos)))
        if lag1 > 0:  # Correlación positiva simple
            tiene_estacionalidad = True

    # Generar sugerencias basadas en el análisis
    sugerencias = []

    if direccion == "creciente":
        sugerencias.append("La tendencia es positiva, considerar estrategias para capitalizar este crecimiento.")
    elif direccion == "decreciente":
        sugerencias.append("La tendencia es negativa, evaluar causas y considerar acciones correctivas.")
    else:
        sugerencias.append("La tendencia es estable, evaluar si esto está alineado con los objetivos.")

    if volatilidad > 0.2 * promedio:
        sugerencias.append("Alta volatilidad detectada, considerar estrategias para estabilizar los resultados.")

    if tiene_estacionalidad:
        sugerencias.append("Se detectan patrones cíclicos, considerar factores estacionales en la planificación.")

    # Construir resultado
    resultado = {
        "estadisticas": {
            "promedio": round(promedio, 2),
            "maximo": round(maximo, 2),
            "minimo": round(minimo, 2),
            "rango": round(rango, 2),
            "volatilidad": round(volatilidad, 2),
        },
        "tendencia": {
            "direccion": direccion,
            "pendiente": round(pendiente, 4),
            "cambio_porcentual": round(cambio_porcentual, 2),
            "tiene_estacionalidad": tiene_estacionalidad,
        },
        "datos_analizados": {"valores": datos, "etiquetas": etiquetas, "num_puntos": len(datos)},
        "sugerencias": sugerencias,
        "fecha_analisis": datetime.now().strftime("%Y-%m-%d"),
    }

    return resultado


async def predecir_valores(datos: list[float], periodos_futuros: int = 3) -> dict[str, Any]:
    """
    Predice valores futuros basados en datos históricos usando tendencias simples.

    Args:
        datos: Serie histórica de valores
        periodos_futuros: Número de periodos a predecir

    Returns:
        Predicciones y confianza del modelo
    """
    if len(datos) < 3:
        return {"error": "Se necesitan al menos tres puntos de datos para hacer predicciones", "success": False}

    if periodos_futuros < 1:
        return {"error": "El número de periodos a predecir debe ser al menos 1", "success": False}

    # Limitar predicciones
    if periodos_futuros > 10:
        periodos_futuros = 10

    # Crear indices
    x = list(range(len(datos)))
    x_pred = list(range(len(datos), len(datos) + periodos_futuros))

    # Calcular tendencia (regresión lineal simple)
    n = len(datos)
    x_mean = sum(x) / n
    y_mean = sum(datos) / n

    numerador = sum((x_i - x_mean) * (y_i - y_mean) for x_i, y_i in zip(x, datos, strict=False))
    denominador = sum((x_i - x_mean) ** 2 for x_i in x)

    if denominador == 0:
        slope = 0
    else:
        slope = numerador / denominador

    intercept = y_mean - slope * x_mean

    # Calcular predicciones
    predicciones = [slope * x_i + intercept for x_i in x_pred]

    # Calcular error del modelo (RMSE)
    predicted_past = [slope * x_i + intercept for x_i in x]
    squared_errors = [(pred - actual) ** 2 for pred, actual in zip(predicted_past, datos, strict=False)]
    rmse = math.sqrt(sum(squared_errors) / len(datos))

    # Calcular r-cuadrado
    ss_total = sum((y - y_mean) ** 2 for y in datos)
    ss_residual = sum(squared_errors)

    if ss_total == 0:
        r_squared = 0
    else:
        r_squared = 1 - (ss_residual / ss_total)

    # Determinar confianza
    if r_squared > 0.8:
        confianza = "alta"
    elif r_squared > 0.5:
        confianza = "media"
    else:
        confianza = "baja"

    # Calcular tasa de crecimiento
    if datos[0] != 0:
        tasa_crecimiento = ((datos[-1] / datos[0]) ** (1 / len(datos)) - 1) * 100
    else:
        tasa_crecimiento = 0

    # Añadir intervalos de confianza simples
    intervalos = []
    factor_error = 1.96 * rmse  # Aproximación para 95% confianza

    for pred in predicciones:
        intervalos.append(
            {
                "inferior": max(0, pred - factor_error),  # Evitar valores negativos si no tienen sentido
                "superior": pred + factor_error,
            }
        )

    # Crear resultado
    resultado = {
        "predicciones": [round(p, 2) for p in predicciones],
        "periodos_predecidos": periodos_futuros,
        "intervalos_confianza": [
            {"inferior": round(i["inferior"], 2), "superior": round(i["superior"], 2)} for i in intervalos
        ],
        "metricas_modelo": {
            "rmse": round(rmse, 4),
            "r_squared": round(r_squared, 4),
            "confianza": confianza,
            "pendiente": round(slope, 4),
            "tasa_crecimiento": round(tasa_crecimiento, 2),
        },
        "datos_originales": {"num_puntos": len(datos), "ultimo_valor": datos[-1], "primer_valor": datos[0]},
        "advertencias": [],
        "fecha_prediccion": datetime.now().strftime("%Y-%m-%d"),
    }

    # Añadir advertencias si es necesario
    if r_squared < 0.5:
        resultado["advertencias"].append(
            "Predicción con baja confianza debido a alta variabilidad en los datos históricos."
        )

    if len(datos) < 5:
        resultado["advertencias"].append(
            "Conjunto de datos pequeño. Se recomiendan al menos 10 puntos para predicciones más confiables."
        )

    if periodos_futuros > len(datos):
        resultado["advertencias"].append(
            "Predecir más periodos que los datos históricos disponibles reduce significativamente la confianza."
        )

    return resultado


async def financial_models(industria: str, metodo: str, datos: dict[str, Any] | None = None) -> dict[str, Any]:
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
    industria_data = modelos_industria.get(industria.lower(), modelos_industria["tecnología"])

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
            comparativa[ind] = {"crecimiento": data["crecimiento_anual"], "margen": data["margen_beneficio_promedio"]}
        return {"industria_base": industria, "metodo": metodo, "comparativa": comparativa}

    else:
        # Método no reconocido, devolver datos generales
        return {
            "industria": industria,
            "datos_financieros": industria_data,
            "nota": "Método no reconocido, se devuelven datos generales de la industria",
        }


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
        "metricas": {"CTR": ctr, "CPC": cpc, "tasa_conversion": conversion_rate, "CPA": cpa, "ROI": roi},
        "evaluacion": {
            "rendimiento_ctr": "Bueno" if ctr > 0.02 else "Regular" if ctr > 0.01 else "Bajo",
            "eficiencia_coste": "Buena" if cpa < 50 else "Regular" if cpa < 100 else "Baja",
            "rentabilidad": "Alta" if roi > 1 else "Media" if roi > 0 else "Baja",
        },
    }

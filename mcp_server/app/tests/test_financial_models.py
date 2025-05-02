"""
Tests para las funcionalidades de financial_models.py
"""

import pytest
from unittest.mock import MagicMock, patch

from app.tools.implementations.financial_models import (
    financial_models,
    calcular_ratios_financieros,
    analizar_rendimiento_campania,
    recomendar_estrategia_marketing,
    analizar_tendencia,
    predecir_valores
)


class TestFinancialModels:
    """Pruebas para las funciones de modelos financieros."""

    @pytest.mark.asyncio
    async def test_calcular_ratios_financieros(self):
        """Prueba que la función calcula correctamente los ratios financieros."""
        # Datos de prueba
        ingresos = 1000000
        beneficio_neto = 200000
        activos_totales = 2000000
        pasivos_totales = 800000
        
        # Ejecutar la función
        resultado = await calcular_ratios_financieros(
            ingresos=ingresos,
            beneficio_neto=beneficio_neto,
            activos_totales=activos_totales,
            pasivos_totales=pasivos_totales
        )
        
        # Verificar resultados - estructura
        assert "ratios" in resultado
        assert "interpretaciones" in resultado
        assert "recomendaciones" in resultado
        assert "fecha_calculo" in resultado
        
        # Verificar ratios específicos
        ratios = resultado["ratios"]
        assert "margen_beneficio" in ratios
        assert "ROA" in ratios
        assert "ROE" in ratios
        assert "ratio_endeudamiento" in ratios
        assert "ratio_liquidez" in ratios
        
        # Verificar cálculos específicos
        assert ratios["margen_beneficio"] == pytest.approx(0.2, abs=0.0001)  # 200,000 / 1,000,000
        assert ratios["ROA"] == pytest.approx(0.1, abs=0.0001)  # 200,000 / 2,000,000
        assert ratios["ROE"] == pytest.approx(0.1667, abs=0.001)  # 200,000 / 1,200,000
        assert ratios["ratio_endeudamiento"] == pytest.approx(0.4, abs=0.0001)  # 800,000 / 2,000,000

    @pytest.mark.asyncio
    async def test_calcular_ratios_financieros_cero(self):
        """Prueba que la función maneja correctamente valores cero."""
        # Datos de prueba con valores cero
        resultado = await calcular_ratios_financieros(
            ingresos=0,
            beneficio_neto=0,
            activos_totales=0,
            pasivos_totales=0
        )
        
        # Verificar resultados
        ratios = resultado["ratios"]
        assert ratios["margen_beneficio"] == 0
        assert ratios["ROA"] == 0
        assert ratios["ROE"] == 0
        assert ratios["ratio_endeudamiento"] == 0
        # No verificamos ratio_liquidez porque puede variar dependiendo de la implementación
        # para evitar division por cero

    @pytest.mark.asyncio
    async def test_analizar_rendimiento_campania(self):
        """Prueba el análisis de rendimiento de campaña."""
        # Datos de prueba
        nombre_campania = "Test Campaign"
        impresiones = 10000
        clics = 500
        conversiones = 50
        coste = 1000
        
        # Ejecutar la función
        resultado = await analizar_rendimiento_campania(
            nombre_campania=nombre_campania,
            impresiones=impresiones,
            clics=clics,
            conversiones=conversiones,
            coste=coste
        )
        
        # Verificar resultados - estructura
        assert "campania" in resultado
        assert "metricas" in resultado
        assert "evaluacion" in resultado
        
        # Verificar que el nombre de la campaña coincide
        assert resultado["campania"] == nombre_campania
        
        # Verificar métricas calculadas
        metricas = resultado["metricas"]
        assert "CTR" in metricas
        assert "CPC" in metricas
        assert "CPA" in metricas
        assert "ROI" in metricas
        
        # Verificar cálculos específicos
        assert metricas["CTR"] == pytest.approx(0.05)  # 500 / 10000
        assert metricas["CPC"] == pytest.approx(2.0)  # 1000 / 500
        assert metricas["CPA"] == pytest.approx(20.0)  # 1000 / 50

    @pytest.mark.asyncio
    async def test_analizar_tendencia(self):
        """Prueba el análisis de tendencias en datos."""
        # Datos de prueba
        datos = [10, 15, 20, 25, 30]
        etiquetas = ["Ene", "Feb", "Mar", "Abr", "May"]
        
        # Ejecutar la función
        resultado = await analizar_tendencia(datos=datos, etiquetas=etiquetas)
        
        # Verificar resultados - estructura
        assert "tendencia" in resultado
        assert "estadisticas" in resultado
        assert "datos_analizados" in resultado
        
        # Verificar tendencia - debería ser creciente para estos datos
        assert "direccion" in resultado["tendencia"]
        assert resultado["tendencia"]["direccion"] == "creciente"
        
        # Verificar estadísticas
        estadisticas = resultado["estadisticas"]
        assert "promedio" in estadisticas
        assert "minimo" in estadisticas
        assert "maximo" in estadisticas
        
        # Verificar valores estadísticos específicos
        assert estadisticas["promedio"] == pytest.approx(20.0)
        assert estadisticas["minimo"] == 10
        assert estadisticas["maximo"] == 30

    @pytest.mark.asyncio
    async def test_predecir_valores(self):
        """Prueba la predicción de valores futuros."""
        # Datos de prueba - tendencia lineal simple
        datos = [10, 20, 30, 40, 50]
        periodos_futuros = 3
        
        # Ejecutar la función
        resultado = await predecir_valores(datos=datos, periodos_futuros=periodos_futuros)
        
        # Verificar resultados - estructura (basado en inspección)
        assert "predicciones" in resultado
        assert "periodos_predecidos" in resultado
        assert "intervalos_confianza" in resultado
        assert "metricas_modelo" in resultado
        assert "datos_originales" in resultado
        assert "advertencias" in resultado
        assert "fecha_prediccion" in resultado
        
        # Verificar que hay 3 predicciones
        assert len(resultado["predicciones"]) == 3
        
        # Las predicciones deberían seguir la tendencia (aproximadamente 60, 70, 80)
        # pero permitiendo cierta variación por el algoritmo usado
        assert 55 <= resultado["predicciones"][0] <= 65
        assert 65 <= resultado["predicciones"][1] <= 75
        assert 75 <= resultado["predicciones"][2] <= 85

    @pytest.mark.asyncio
    async def test_recomendar_estrategia_marketing(self):
        """Prueba la recomendación de estrategias de marketing."""
        # Datos de prueba
        industria = "tecnologia"
        presupuesto = 10000
        objetivo = "brand_awareness"
        publico_objetivo = "jovenes_profesionales"
        
        # Ejecutar la función
        resultado = await recomendar_estrategia_marketing(
            industria=industria,
            presupuesto=presupuesto,
            objetivo=objetivo,
            publico_objetivo=publico_objetivo
        )
        
        # Verificar resultados - estructura (basado en inspección)
        assert "industria" in resultado
        assert "objetivo" in resultado
        assert "canales_recomendados" in resultado
        assert "distribucion_presupuesto" in resultado
        assert "calendario_sugerido" in resultado
        assert "fecha_recomendacion" in resultado
        assert "presupuesto_total" in resultado
        
        # Verificar que la suma de la distribución del presupuesto es 100%
        assert sum(resultado["distribucion_presupuesto"].values()) == pytest.approx(100.0)
        
        # Verificar que hay canales recomendados
        assert len(resultado["canales_recomendados"]) > 0
        
        # Verificar que hay calendario sugerido
        assert len(resultado["calendario_sugerido"]) > 0

    @pytest.mark.asyncio
    async def test_financial_models_general(self):
        """Prueba el modelo financiero con datos generales."""
        # Datos de prueba
        industria = "tecnologia"
        metodo = "general"  # Método general debería funcionar siempre
        datos = None
        
        # Ejecutar la función
        resultado = await financial_models(industria=industria, metodo=metodo, datos=datos)
        
        # Verificar resultados - estructura
        assert "industria" in resultado
        assert "datos_financieros" in resultado
        
        # Verificar que la industria coincide
        assert resultado["industria"] == "tecnologia"
        
        # Verificar que hay datos financieros
        datos_financieros = resultado["datos_financieros"]
        assert len(datos_financieros) > 0
        
        # Verificar algunas métricas comunes
        expected_keys = ["crecimiento_anual", "margen_beneficio_promedio", "roi_esperado"]
        for key in expected_keys:
            assert key in datos_financieros 
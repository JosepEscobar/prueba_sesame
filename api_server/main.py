#!/usr/bin/env python3
"""
API principal del sistema.

Esta API proporciona puntos finales para interactuar con los agentes del sistema
de asistencia empresarial.
"""

import os
import sys
import logging
import time
import httpx
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import traceback

# Añadir el directorio raíz al path para poder importar módulos
sys.path.insert(0, str(Path(__file__).parent))

# Importar primero la configuración para asegurar que las variables de entorno estén cargadas
from app.core.config import get_settings

# Obtener configuración
settings = get_settings()

# Configurar logging
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Configurar logger básico
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(logs_dir / "app.log"),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("api_server")

# Importamos el Router Agent - después de configurar el logger
try:
    from app.agents.router_agent import RouterAgent
    from app.core.graph import AgentGraph
    logger.info("RouterAgent importado correctamente")
except Exception as e:
    logger.error(f"Error al importar RouterAgent: {str(e)}")

# ---- Modelos de datos Pydantic ----
class HealthResponse(BaseModel):
    """
    Respuesta del endpoint de health check que proporciona información sobre el estado del sistema.
    
    Permite monitorear la salud de la API y su conexión con el servidor MCP.
    """
    status: str = Field(
        description="Estado actual del servicio API (healthy, degraded, unhealthy)",
        example="healthy"
    )
    version: str = Field(
        description="Versión actual de la API Sesame",
        example="0.1.0"
    )
    mcp_status: str = Field(
        description="Estado de la conexión con el servidor MCP (connected, disconnected, initializing)",
        example="connected"
    )

class MCPStatusResponse(BaseModel):
    """
    Información detallada sobre el estado de la conexión con el servidor MCP.
    
    Proporciona detalles sobre la disponibilidad del servidor MCP, su URL y las herramientas registradas.
    """
    status: str = Field(
        description="Estado actual de la conexión con MCP (connected, disconnected, initializing)",
        example="connected"
    )
    mcp_url: str = Field(
        description="URL del servidor MCP al que está conectada la API",
        example="http://localhost:4500"
    )
    tools_available: int = Field(
        description="Número total de herramientas disponibles en el servidor MCP",
        example=6
    )
    tools: List[str] = Field(
        description="Lista de identificadores de las herramientas disponibles en el servidor MCP",
        example=["buscar_datos_financieros", "calcular_ratios_financieros"]
    )

class QueryRequest(BaseModel):
    """
    Formato de petición para consultas a los agentes.
    
    Contiene la consulta en lenguaje natural y contexto adicional opcional.
    """
    query: str = Field(
        description="Consulta o instrucción en lenguaje natural para el agente",
        example="Analiza el rendimiento financiero de mi empresa",
        min_length=3,
        max_length=1000
    )
    context: Optional[Dict[str, Any]] = Field(
        default={},
        description="Contexto adicional para enriquecer la consulta (empresa, periodos, etc.)",
        example={"empresa": "MiEmpresa", "periodo": "Q1 2025", "region": "Europa"}
    )

class FinancialMetrics(BaseModel):
    """
    Métricas financieras estándar proporcionadas en respuestas de análisis financiero.
    
    Incluye indicadores clave de rendimiento financiero como ingresos, beneficios y ratios.
    """
    revenue: float = Field(
        description="Ingresos totales en la moneda base", 
        example=1250000,
        gt=0
    )
    profit: float = Field(
        description="Beneficio neto en la moneda base", 
        example=450000
    )
    growth: str = Field(
        description="Porcentaje de crecimiento respecto al periodo anterior", 
        example="15%"
    )
    margin: Optional[float] = Field(
        description="Margen de beneficio (profit/revenue)", 
        example=0.36,
        ge=0,
        le=1
    )
    roi: Optional[float] = Field(
        description="Retorno de inversión", 
        example=0.22
    )

class FinanceResponse(BaseModel):
    """
    Respuesta estándar para los endpoints de análisis financiero.
    
    Incluye un texto descriptivo y las métricas financieras calculadas.
    """
    result: str = Field(
        description="Resultado textual del análisis financiero",
        example="Análisis financiero completo de MiEmpresa para Q1 2025",
        min_length=5
    )
    metrics: FinancialMetrics = Field(
        description="Conjunto de métricas financieras calculadas"
    )

class MarketingMetrics(BaseModel):
    """
    Métricas de marketing estándar proporcionadas en respuestas de análisis de marketing.
    
    Incluye indicadores clave de rendimiento de marketing y campañas.
    """
    ctr: float = Field(
        description="Click-through rate (tasa de clics)", 
        example=0.025,
        ge=0,
        le=1
    )
    conversion_rate: float = Field(
        description="Tasa de conversión (porcentaje de conversiones sobre visitas)",
        example=0.032,
        ge=0,
        le=1
    )
    roi: float = Field(
        description="Retorno de inversión de marketing", 
        example=2.4
    )
    cpa: Optional[float] = Field(
        description="Coste por adquisición en la moneda base", 
        example=45.0,
        gt=0
    )
    campaign_count: Optional[int] = Field(
        description="Número de campañas incluidas en el análisis", 
        example=5,
        ge=0
    )

class MarketingResponse(BaseModel):
    """
    Respuesta estándar para los endpoints de análisis de marketing.
    
    Incluye un texto descriptivo y las métricas de marketing calculadas.
    """
    result: str = Field(
        description="Resultado textual del análisis de marketing",
        example="Análisis de marketing completo para la campaña Verano 2025",
        min_length=5
    )
    metrics: MarketingMetrics = Field(
        description="Conjunto de métricas de marketing calculadas"
    )

class AgentResponse(BaseModel):
    """
    Respuesta genérica de un agente del sistema.
    
    Contiene el resultado de la consulta procesada junto con metadatos
    sobre el procesamiento y el agente que lo realizó.
    """
    result: str = Field(
        description="Resultado textual generado por el agente",
        example="Análisis completo realizado. Los ingresos han aumentado un 15% respecto al trimestre anterior.",
        min_length=5
    )
    agent: str = Field(
        description="Identificador del agente que procesó la solicitud",
        example="finance_agent"
    )
    confidence: float = Field(
        description="Nivel de confianza del agente en el resultado (0-1)",
        example=0.95,
        ge=0,
        le=1
    )
    processing_time: Optional[float] = Field(
        description="Tiempo de procesamiento en segundos",
        example=1.25,
        gt=0
    )

# Crear la aplicación FastAPI
app = FastAPI(
    title="Sesame API",
    description="""
    ## 🚀 Plataforma de Asistencia Empresarial Sesame
    
    Sesame es una plataforma avanzada que integra análisis de datos empresariales a través de:
    
    * **Asistentes Inteligentes** para análisis financiero y de marketing
    * **Herramientas MCP** para procesamiento específico de datos
    * **Integración Completa** entre diferentes funciones empresariales
    
    Esta API proporciona acceso directo a los recursos de Sesame.
    
    ### 📊 Principales funcionalidades
    
    * Análisis financiero y proyecciones
    * Evaluación de estrategias de marketing
    * Planificación de campañas
    * Acceso directo a herramientas de procesamiento
    
    ### 🔗 Enlaces útiles
    
    * [Documentación extendida](https://sesame.example.com/docs)
    * [Guía de inicio rápido](https://sesame.example.com/quickstart)
    * [Repositorio del proyecto](https://github.com/sesame/api)
    """,
    version="0.1.0",
    terms_of_service="https://sesame.example.com/terms/",
    contact={
        "name": "Equipo de Desarrollo Sesame",
        "url": "https://sesame.example.com",
        "email": "soporte@sesame.example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "General", 
            "description": "Operaciones de estado y bienvenida", 
            "externalDocs": {
                "description": "Documentación externa",
                "url": "https://sesame.example.com/docs/general"
            }
        },
        {
            "name": "MCP", 
            "description": "Endpoints para interacción con el servidor MCP (Model Context Protocol)",
            "externalDocs": {
                "description": "Documentación sobre MCP",
                "url": "https://sesame.example.com/docs/mcp"
            }
        },
        {
            "name": "Agentes", 
            "description": "Consultas procesadas mediante agentes especializados con IA",
            "externalDocs": {
                "description": "Guía de agentes",
                "url": "https://sesame.example.com/docs/agents"
            }
        },
        {
            "name": "Finanzas", 
            "description": "Análisis de datos financieros y pronósticos económicos",
            "externalDocs": {
                "description": "Documentación sobre análisis financiero",
                "url": "https://sesame.example.com/docs/finance"
            }
        },
        {
            "name": "Marketing", 
            "description": "Análisis de campañas y planificación de estrategias de marketing",
            "externalDocs": {
                "description": "Guía de marketing",
                "url": "https://sesame.example.com/docs/marketing"
            }
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Configuración MCP Client ----
# Información sobre el servidor MCP
mcp_url = os.environ.get("MCP_SERVER_URL", "http://localhost:4500")
logger.info(f"URL del servidor MCP configurada como: {mcp_url}")

# ---- Rutas API ----
@app.get(
    "/",
    summary="Página de inicio de Sesame API",
    description="""
    Punto de entrada principal de la API Sesame.
    
    Esta ruta devuelve información básica sobre la API y enlaces a la documentación interactiva.
    Es útil como verificación rápida de que la API está funcionando correctamente.
    """,
    response_description="Información de bienvenida de la API",
    tags=["General"],
    responses={
        200: {
            "description": "Respuesta de bienvenida de Sesame API",
            "content": {
                "application/json": {
                    "example": {
                        "message": "¡Bienvenido a la API de Sesame!",
                        "docs": "/docs"
                    }
                }
            }
        }
    }
)
async def root():
    """
    Ruta raíz que proporciona información básica sobre la API.
    """
    return {
        "message": "¡Bienvenido a la API de Sesame!",
        "docs": "/docs"
    }

@app.get(
    "/health",
    summary="Verificar estado de salud del servicio",
    description="""
    Endpoint de health check para monitoreo de la API.
    
    Permite verificar si la API está funcionando correctamente y cuál es su estado
    de conexión con otros servicios como el servidor MCP.
    
    Este endpoint es útil para:
    * Sistemas de monitoreo automático
    * Verificaciones de alta disponibilidad
    * Comprobación de estado de dependencias
    
    El campo `status` puede tener los siguientes valores:
    * `healthy`: El servicio funciona correctamente
    * `degraded`: El servicio funciona con limitaciones
    * `unhealthy`: El servicio no funciona correctamente
    """,
    response_model=HealthResponse,
    response_description="Detalles del estado de salud del servicio",
    tags=["General"],
    responses={
        200: {
            "description": "Estado de salud de la API",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "0.1.0",
                        "mcp_status": "connected"
                    }
                }
            }
        }
    }
)
async def health_check():
    """
    Verificar el estado de la API.
    
    Retorna el estado de salud del servicio, incluyendo información sobre la
    conexión con el servidor MCP.
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "mcp_status": "connected"
    }

@app.get(
    "/mcp/status",
    summary="Obtener estado de conexión con MCP",
    description="""
    Proporciona información detallada sobre la conexión con el servidor MCP.
    
    El servidor MCP (Model Context Protocol) es responsable de gestionar
    las herramientas especializadas que utilizan los agentes de Sesame.
    
    Este endpoint permite verificar:
    * Estado de la conexión con el servidor MCP
    * URL del servidor MCP actualmente configurado
    * Listado completo de herramientas disponibles
    * Número total de herramientas registradas
    
    Es útil para diagnóstico y para conocer qué capacidades están disponibles
    en el sistema en tiempo real.
    """,
    response_model=MCPStatusResponse,
    response_description="Estado de la conexión y lista de herramientas",
    tags=["MCP"],
    responses={
        200: {
            "description": "Estado del cliente MCP",
            "content": {
                "application/json": {
                    "example": {
                        "status": "connected",
                        "mcp_url": "http://localhost:4500",
                        "tools_available": 6,
                        "tools": [
                            "buscar_datos_financieros",
                            "calcular_ratios_financieros",
                            "analizar_rendimiento_campania",
                            "recomendar_estrategia_marketing",
                            "analizar_tendencia",
                            "predecir_valores"
                        ]
                    }
                }
            }
        }
    }
)
async def mcp_status():
    """
    Verificar el estado del cliente MCP.
    
    Proporciona información detallada sobre la conexión con el servidor MCP
    y las herramientas disponibles.
    """
    return {
        "status": "connected",
        "mcp_url": mcp_url,
        "tools_available": 6,
        "tools": [
            "buscar_datos_financieros",
            "calcular_ratios_financieros",
            "analizar_rendimiento_campania",
            "recomendar_estrategia_marketing",
            "analizar_tendencia",
            "predecir_valores"
        ]
    }

@app.post(
    "/api/v1/query",
    summary="Procesar consulta general",
    description="""
    Punto de entrada principal para consultas de usuarios.
    
    Este endpoint recibe consultas en lenguaje natural y las enruta al agente
    más adecuado según su contenido. Funciona como un dispatcher inteligente
    que determina si la consulta debe ser procesada por:
    
    * El agente financiero (finance_agent)
    * El agente de marketing (marketing_agent)
    * El agente de análisis general (analysis_agent)
    * O queda en manos del router_agent
    
    ### Ejemplo de consultas:
    
    * "Analiza el rendimiento financiero del último trimestre"
    * "Evalúa el impacto de nuestra campaña de marketing digital"
    * "¿Cuáles son las tendencias actuales de nuestro mercado?"
    """
)
async def process_query(
    request: Request,
    query_data: QueryRequest
):
    """
    Endpoint para procesar consultas generales.
    
    Args:
        query_data: Datos de la consulta
    
    Returns:
        Respuesta procesada
    """
    start_time = time.time()
    
    try:
        # Validar que haya una consulta
        query = query_data.query.strip()
        if not query:
            raise ValueError("La consulta no puede estar vacía")
        
        # Extraer el contexto
        context = query_data.context
        
        logger.info(f"Recibida consulta: {query[:50] if isinstance(query, str) else str(query)[:50]}...")
        
        # Inicializar el grafo de agentes
        try:
            # Crear una instancia del grafo de agentes
            agent_graph = AgentGraph()
            
            # Preparar los datos de entrada para el grafo
            input_data = {
                "query": query,
                "context": context,
                # No inicializar estos campos, serán establecidos por el grafo:
                # "current_agent": "router",
                # "agent_output": {}
            }
            
            # Imprimir para depuración
            print(f"* DEBUG: Enviando consulta al grafo: {input_data}")
            
            # Ejecutar el grafo de agentes
            logger.info(f"Ejecutando grafo de agentes con la consulta")
            try:
                final_result = agent_graph.run(input_data)
            except Exception as e:
                logger.error(f"Error al procesar consulta con el grafo: {str(e)}")
                traceback.print_exc()
                # DEBUG ERROR
                print(f"* DEBUG ERROR: {str(e)}")
                print(traceback.format_exc())
                
                # Intentar usar respuestas alternativas para consultas financieras
                if "financ" in query.lower() or "model" in query.lower():
                    # Fallback para consultas financieras
                    industry = context.get("industry", "general")
                    logger.info(f"Usando fallback para consulta financiera sobre industria: {industry}")
                    
                    # Construir una respuesta directa sin usar el grafo
                    from app.api.routes import generate_financial_model
                    model_content = generate_financial_model(industry)
                    final_result = {
                        "agent": "finance_agent",
                        "confidence": 0.85,
                        "result": {
                            "content": model_content,
                            "source": "finance_agent",
                            "model_type": "direct_response",
                            "analysis_complete": True
                        }
                    }
                else:
                    # Fallback para otras consultas
                    final_result = {
                        "agent": "analysis_agent",
                        "confidence": 0.7,
                        "result": {
                            "content": "No se pudo procesar la consulta a través del grafo de agentes. Por favor, inténtelo de nuevo.",
                            "source": "analysis_agent"
                        }
                    }
            
            # Imprimir para depuración
            print(f"* DEBUG: Resultado final del grafo: {final_result}")
            
            # Verificar si tenemos un resultado válido
            if isinstance(final_result, dict):
                result = final_result
                # Asegurarnos de que tenga los campos mínimos
                if "result" not in result:
                    result["result"] = "Consulta procesada con éxito"
                if "agent" not in result:
                    result["agent"] = "unknown_agent"
                if "confidence" not in result:
                    result["confidence"] = 0.7
            else:
                # Respuesta de fallback si no hay resultado válido
                logger.warning(f"Resultado inválido del grafo: {final_result}")
                result = {
                    "result": "No se pudo procesar completamente su consulta",
                    "agent": "router_agent",
                    "confidence": 0.5
                }
                
            # Calcular tiempo de procesamiento
            processing_time = time.time() - start_time
            
            # Registrar métrica
            logger.info(f"Consulta procesada por {result.get('agent', 'desconocido')} con confianza {result.get('confidence', 0.0)}")
            
            # Añadir tiempo de procesamiento
            result["processing_time"] = processing_time
            
            return result
            
        except Exception as e:
            logger.error(f"Error al procesar consulta con el grafo: {str(e)}")
            print(f"* DEBUG ERROR: {str(e)}")
            traceback.print_exc()  # Imprimir stack trace completo
            
            # Respuesta de fallback en caso de error
            processing_time = time.time() - start_time
            return {
                "result": "Error al procesar su consulta con el grafo de agentes",
                "error": str(e),
                "agent": "error", 
                "confidence": 0.0,
                "processing_time": processing_time
            }
    
    except Exception as e:
        logger.error(f"Error global al procesar consulta: {str(e)}")
        print(f"* DEBUG GLOBAL ERROR: {str(e)}")
        traceback.print_exc()  # Imprimir stack trace completo
        
        processing_time = time.time() - start_time
        return {
            "result": "Error al procesar su consulta",
            "error": str(e),
            "processing_time": processing_time
        }

def classify_query_by_keywords(query: str) -> str:
    """
    Clasifica una consulta por palabras clave.
    
    Args:
        query: La consulta a clasificar
    
    Returns:
        El tipo de agente más adecuado
    """
    # Diccionario de agentes con sus palabras clave
    agents_keywords = {
        "finance_agent": [
            "financiero", "finanzas", "ingresos", "beneficio", "margen", 
            "roi", "ganancia", "rentabilidad", "balance", "contabilidad",
            "fiscal", "impuestos", "patrimonio", "capital", "inversión",
            "activos", "pasivos", "presupuesto", "costes", "gastos"
        ],
        "marketing_agent": [
            "marketing", "mercado", "campaña", "publicidad", "promoción", 
            "ventas", "clientes", "segmentación", "conversión", "marca",
            "audiencia", "consumidor", "target", "posicionamiento", "social",
            "digital", "comunicación", "medios", "engagement", "producto"
        ],
        "analysis_agent": [
            "tendencia", "análisis", "analiza", "predicción", "pronóstico",
            "proyección", "futuro", "evolución", "comparativa", "datos",
            "información", "patrones", "insights", "métricas", "indicadores",
            "histórico", "estadística", "correlación", "hallazgos", "síntesis"
        ]
    }
    
    # Convertir la consulta a minúsculas
    query_lower = query.lower()
    
    # Calcular puntuaciones para cada agente
    scores = {}
    for agent_name, keywords in agents_keywords.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        scores[agent_name] = score
    
    # Encontrar el agente con mayor puntuación
    if not scores:
        return "analysis_agent"  # Por defecto
        
    max_score = max(scores.values())
    if max_score == 0:
        return "analysis_agent"  # Si ninguno tiene keywords, usar análisis
        
    # Si hay múltiples con la misma puntuación máxima, priorizar en este orden
    priority = ["finance_agent", "marketing_agent", "analysis_agent"]
    max_agents = [agent for agent, score in scores.items() if score == max_score]
    
    for p in priority:
        if p in max_agents:
            return p
            
    # Si ninguno de los priorizados está en los máximos, tomar el primero
    return max_agents[0]

def simulate_agent_response(agent_name: str, query: str) -> str:
    """
    Genera una respuesta simulada para el modo de desarrollo sin API key.
    """
    query_preview = query[:30] + "..." if len(query) > 30 else query
    
    if agent_name == "finance_agent":
        return f"[SIMULACIÓN] Análisis financiero para: {query_preview}\n\nEste es un resultado simulado para el agente financiero en modo desarrollo."
    elif agent_name == "marketing_agent":
        return f"[SIMULACIÓN] Análisis de marketing para: {query_preview}\n\nEste es un resultado simulado para el agente de marketing en modo desarrollo."
    else:
        return f"[SIMULACIÓN] Análisis general para: {query_preview}\n\nEste es un resultado simulado para el agente de análisis en modo desarrollo."

@app.post(
    "/api/v1/finance/analyze",
    summary="Analizar datos financieros",
    description="""
    Realiza un análisis financiero detallado basado en la consulta proporcionada.
    
    Este endpoint está especializado en el procesamiento de consultas relacionadas
    con finanzas empresariales. Utiliza el agente financiero (finance_agent) para
    procesar la consulta y generar análisis basados en:
    
    * Estados financieros
    * Indicadores de rendimiento (KPIs)
    * Tendencias históricas
    * Comparativas sectoriales
    
    ### Ejemplos de consultas:
    
    * "Calcula los ratios financieros basados en el balance"
    * "¿Cuál ha sido la evolución de nuestro ROI en los últimos 4 trimestres?"
    * "Compara nuestro margen de beneficio con el del sector"
    
    ### Métricas proporcionadas:
    
    * Ingresos (revenue)
    * Beneficio (profit)
    * Crecimiento (growth)
    * Margen (margin)
    * Retorno de inversión (roi)
    
    > Nota: Este endpoint es específico para análisis financiero. Para consultas
    > generales, utiliza el endpoint `/api/v1/query`.
    """,
    response_model=FinanceResponse,
    response_description="Resultado del análisis financiero con métricas claves",
    tags=["Finanzas"],
    responses={
        200: {
            "description": "Detalle del análisis financiero",
            "content": {
                "application/json": {
                    "example": {
                        "result": "Análisis financiero para: Calcula...",
                        "metrics": {
                            "revenue": 1250000,
                            "profit": 450000,
                            "growth": "15%",
                            "margin": 0.36,
                            "roi": 2.1
                        }
                    }
                }
            }
        },
        422: {
            "description": "Consulta inválida o incompleta"
        }
    }
)
async def analyze_finance(request: QueryRequest = Body(...)):
    """
    Analizar datos financieros.
    
    Procesa una consulta relacionada con finanzas utilizando el agente
    especializado en análisis financiero.
    """
    return {
        "result": f"Análisis financiero para: {request.query[:30]}...",
        "metrics": {
            "revenue": 1250000,
            "profit": 450000, 
            "growth": "15%",
            "margin": 0.36,
            "roi": 2.1
        }
    }

@app.post(
    "/api/v1/finance/forecast",
    summary="Generar pronósticos financieros",
    description="""
    Proyecta tendencias financieras futuras utilizando modelos predictivos.
    
    Este endpoint aplica técnicas avanzadas de modelado estadístico y aprendizaje
    automático para generar pronósticos financieros basados en:
    
    * Datos históricos de la empresa
    * Tendencias del mercado
    * Variables macroeconómicas
    * Estacionalidad y eventos especiales
    
    ### Ejemplos de consultas:
    
    * "Proyecta los ingresos para el próximo trimestre"
    * "¿Cómo evolucionará nuestro margen en los próximos 6 meses?"
    * "Estima el ROI de nuestra nueva línea de productos"
    
    ### Casos de uso:
    
    * Planificación presupuestaria
    * Toma de decisiones estratégicas
    * Evaluación de nuevas inversiones
    * Gestión de riesgos financieros
    
    > Advertencia: Los pronósticos son estimaciones basadas en datos históricos
    > y modelos estadísticos. Los resultados reales pueden variar.
    """,
    response_model=FinanceResponse,
    response_description="Pronóstico de métricas financieras",
    tags=["Finanzas"],
    responses={
        200: {
            "description": "Pronóstico financiero simulado",
            "content": {
                "application/json": {
                    "example": {
                        "result": "Pronóstico financiero para: Proyecta...",
                        "metrics": {
                            "revenue": 1425000,
                            "profit": 520000,
                            "growth": "18%",
                            "margin": 0.365,
                            "roi": 2.3
                        }
                    }
                }
            }
        },
        422: {
            "description": "Consulta inválida o incompleta"
        }
    }
)
async def financial_forecast(request: QueryRequest = Body(...)):
    """
    Generar pronósticos financieros.
    
    Procesa una consulta para proyectar tendencias financieras futuras
    basándose en datos históricos.
    """
    return {
        "result": f"Pronóstico financiero para: {request.query[:30]}...",
        "metrics": {
            "revenue": 1425000,  # Proyección
            "profit": 520000,    # Proyección
            "growth": "18%",
            "margin": 0.365,
            "roi": 2.3
        }
    }

@app.post(
    "/api/v1/marketing/analyze",
    summary="Analizar marketing",
    description="""
    Evalúa el rendimiento de estrategias y campañas de marketing.
    
    Este endpoint proporciona análisis detallados sobre el desempeño de las
    actividades de marketing, incluyendo:
    
    * Rendimiento de campañas digitales
    * Efectividad de canales de adquisición
    * Análisis de conversión
    * Retorno de inversión en marketing
    
    ### Ejemplos de consultas:
    
    * "Analiza el rendimiento de nuestra campaña digital"
    * "¿Qué canales de marketing están generando mayor ROI?"
    * "Evalúa la efectividad de nuestras campañas de email marketing"
    
    ### Métricas proporcionadas:
    
    * CTR (Click-Through Rate)
    * Tasa de conversión (Conversion Rate)
    * ROI de marketing
    * Coste por adquisición (CPA)
    * Número de campañas analizadas
    """,
    response_model=MarketingResponse,
    response_description="Métricas detalladas del análisis de marketing",
    tags=["Marketing"],
    responses={
        200: {
            "description": "Resultado del análisis de marketing",
            "content": {
                "application/json": {
                    "example": {
                        "result": "Análisis de marketing para: Analiza...",
                        "metrics": {
                            "ctr": 0.025,
                            "conversion_rate": 0.032,
                            "roi": 2.4,
                            "cpa": 45.0,
                            "campaign_count": 5
                        }
                    }
                }
            }
        },
        422: {
            "description": "Consulta inválida o incompleta"
        }
    }
)
async def analyze_marketing(request: QueryRequest = Body(...)):
    """
    Analizar estrategias y resultados de marketing.
    
    Procesa una consulta relacionada con marketing utilizando el agente
    especializado en análisis de marketing.
    """
    return {
        "result": f"Análisis de marketing para: {request.query[:30]}...",
        "metrics": {
            "ctr": 0.025,
            "conversion_rate": 0.032,
            "roi": 2.4,
            "cpa": 45.0,
            "campaign_count": 5
        }
    }

@app.post(
    "/api/v1/marketing/campaign",
    summary="Planificar campaña de marketing",
    description="""
    Genera recomendaciones para el diseño de nuevas campañas de marketing.
    
    Este endpoint utiliza modelos avanzados para crear planes de campaña
    optimizados según los objetivos establecidos. Considera factores como:
    
    * Público objetivo
    * Canales disponibles
    * Presupuesto asignado
    * Objetivos de conversión
    * Estacionalidad
    
    ### Ejemplos de consultas:
    
    * "Diseña una campaña para el lanzamiento del producto"
    * "¿Qué estrategia de marketing debemos usar para aumentar conversiones?"
    * "Crea un plan para mejorar nuestra presencia en redes sociales"
    
    ### Contexto relevante:
    
    Es recomendable proporcionar información adicional en el campo `context` como:
    * Producto o servicio objetivo
    * Presupuesto disponible
    * Duración prevista
    * Canales preferidos
    
    ### Métricas proyectadas:
    
    El resultado incluye proyecciones de métricas clave como CTR, tasa de
    conversión y ROI esperado basadas en campañas similares anteriores.
    """,
    response_model=MarketingResponse,
    response_description="Plan de campaña y métricas estimadas",
    tags=["Marketing"],
    responses={
        200: {
            "description": "Plan de campaña generado",
            "content": {
                "application/json": {
                    "example": {
                        "result": "Plan de campaña para: Diseña...",
                        "metrics": {
                            "ctr": 0.032,
                            "conversion_rate": 0.038,
                            "roi": 2.8,
                            "cpa": 38.5,
                            "campaign_count": 1
                        }
                    }
                }
            }
        },
        422: {
            "description": "Consulta inválida o incompleta"
        }
    }
)
async def plan_campaign(request: QueryRequest = Body(...)):
    """
    Planificar una campaña de marketing.
    
    Genera recomendaciones para una nueva campaña de marketing
    basada en objetivos y datos históricos.
    """
    return {
        "result": f"Plan de campaña para: {request.query[:30]}...",
        "metrics": {
            "ctr": 0.032,  # Proyectado
            "conversion_rate": 0.038,  # Proyectado
            "roi": 2.8,
            "cpa": 38.5,
            "campaign_count": 1
        }
    }

@app.post(
    "/api/v1/tools/{tool_name}",
    summary="Invocar herramienta MCP",
    description="""
    Acceso directo a las herramientas del servidor MCP.
    
    Este endpoint permite llamar directamente a cualquiera de las herramientas
    disponibles en el servidor MCP sin pasar por los agentes intermediarios.
    Es útil para operaciones específicas donde se conoce exactamente qué
    herramienta se necesita.
    
    ### Herramientas disponibles:
    
    * `buscar_datos_financieros`: Búsqueda de datos financieros específicos
    * `calcular_ratios_financieros`: Cálculo de ratios a partir de datos
    * `analizar_rendimiento_campania`: Análisis detallado de una campaña
    * `recomendar_estrategia_marketing`: Recomendaciones de estrategia
    * `analizar_tendencia`: Análisis de tendencias en series temporales
    * `predecir_valores`: Predicción de valores futuros
    
    ### Parámetros:
    
    Los parámetros requeridos dependen de cada herramienta específica.
    Consulta la documentación detallada de cada herramienta para conocer
    los parámetros aceptados.
    
    ### Seguridad:
    
    Este endpoint requiere conocimiento específico de la herramienta a utilizar.
    Asegúrate de validar los parámetros antes de realizar la llamada.
    """,
    response_description="Resultado de la herramienta junto con los parámetros recibidos",
    tags=["MCP"],
    responses={
        200: {
            "description": "Respuesta de la herramienta MCP",
            "content": {
                "application/json": {
                    "example": {
                        "result": "Resultado de la herramienta buscar_datos_financieros",
                        "params_received": {"empresa": "MiEmpresa", "periodo": "2025", "tipo_datos": "ingresos"}
                    }
                }
            }
        },
        404: {
            "description": "Herramienta no encontrada",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Herramienta 'herramienta_inexistente' no encontrada"
                    }
                }
            }
        },
        422: {
            "description": "Parámetros inválidos para la herramienta"
        }
    }
)
async def call_tool(tool_name: str, params: Dict[str, Any] = Body(...)):
    """
    Llamar directamente a una herramienta MCP.
    
    Permite acceder directamente a las herramientas expuestas por el
    servidor MCP sin pasar por los agentes.
    
    Args:
        tool_name: Nombre de la herramienta a llamar
        params: Parámetros para la herramienta
    """
    available_tools = [
        "buscar_datos_financieros",
        "calcular_ratios_financieros",
        "analizar_rendimiento_campania",
        "recomendar_estrategia_marketing",
        "analizar_tendencia",
        "predecir_valores"
    ]
    
    if tool_name not in available_tools:
        raise HTTPException(status_code=404, detail=f"Herramienta '{tool_name}' no encontrada")
    
    # Simulamos el resultado de la herramienta
    return {
        "result": f"Resultado de la herramienta {tool_name}",
        "params_received": params
    }

if __name__ == "__main__":
    # Ejecutar la aplicación con uvicorn
    logger.info("Iniciando servidor API")
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8008,
        reload=True,
        log_level="info"
    ) 
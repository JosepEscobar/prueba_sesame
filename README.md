# Sistema Multi-Agente con LangGraph y FastAPI

Sistema avanzado de agentes inteligentes construido con LangGraph y FastAPI, diseñado para procesamiento de consultas y análisis empresarial.

## Características principales

- **Arquitectura multi-agente** basada en LangGraph, que permite flujos de trabajo dinámicos y complejos
- **Router dinámico** que analiza las consultas y las dirige al agente especializado más adecuado
- **Agentes especializados** para distintos tipos de tareas:
  - **Router Agent**: Clasifica consultas y las dirige al agente apropiado 
  - **Analysis Agent**: Análisis detallado de información y situaciones empresariales
  - **Action Agent**: Recomendaciones prácticas y planes de acción
  - **Summary Agent**: Síntesis de información compleja en formato conciso
  - **Finance Agent**: Análisis financiero y consultoría económica
  - **Marketing Agent**: Estrategias de marketing y análisis de mercado
- **Integración con fuentes de datos externas** a través del servicio DataLookupService
- **Logging estructurado** en formato JSON para mejor observabilidad
- **Sistema de métricas** basado en Prometheus para monitorización de rendimiento
- **API RESTful** con FastAPI para interacción con el sistema
- **Soporte para Model Context Protocol (MCP)** para integración de herramientas externas

## Estructura del proyecto

```
app/
├── agents/                   # Implementación de los agentes del sistema
│   ├── action_agent.py       # Agente especializado en acciones y recomendaciones
│   ├── analysis_agent.py     # Agente especializado en análisis de información
│   ├── base.py               # Clase base para todos los agentes
│   ├── finance_agent.py      # Agente especializado en análisis financiero
│   ├── marketing_agent.py    # Agente especializado en estrategias de marketing
│   ├── router_agent.py       # Agente que clasifica y enruta las consultas
│   └── summary_agent.py      # Agente que genera resúmenes concisos
├── api/                      # Definición de la API REST
│   ├── models.py             # Modelos de datos para la API
│   └── router.py             # Enrutador principal de la API
├── core/                     # Componentes principales del sistema
│   ├── config.py             # Configuración centralizada
│   ├── graph.py              # Definición del grafo de agentes con LangGraph
│   ├── logging.py            # Configuración de logging estructurado
│   ├── metrics.py            # Sistema de métricas y monitoreo
│   └── orchestrator.py       # Orquestador del sistema multi-agente
├── services/                 # Servicios externos e integraciones
│   └── data_lookup.py        # Servicio para búsqueda en fuentes de datos externas
├── tools/                    # Herramientas utilizadas por los agentes
│   └── mcp_client.py         # Cliente para Model Context Protocol
├── tests/                    # Tests automatizados
├── main.py                   # Punto de entrada de la aplicación
└── requirements.txt          # Dependencias del proyecto
```

## Instalación

### Prerrequisitos

- Python 3.10+
- pip

### Instalación de dependencias

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows usar: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Configuración

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:

```
OPENAI_API_KEY=tu_api_key
ALPHA_VANTAGE_API_KEY=tu_api_key    # Para datos financieros
NEWS_API_KEY=tu_api_key              # Para búsqueda de noticias
BING_SEARCH_API_KEY=tu_api_key       # Para búsqueda web
```

## Uso

### Iniciar el servidor

```bash
uvicorn app.main:app --reload
```

Una vez iniciado, la API estará disponible en `http://localhost:8000`.

### Endpoints principales

- `GET /api/v1/agents`: Lista todos los agentes disponibles y sus capacidades
- `POST /api/v1/query`: Procesa una consulta utilizando el sistema multi-agente

### Ejemplo de consulta

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Cuáles son las mejores estrategias de marketing digital para una startup de fintech?",
    "context": {
      "industry": "fintech",
      "target_market": "millennials",
      "budget": "limitado",
      "competitors": ["Revolut", "N26", "Wise"]
    }
  }'
```

## Servicios Integrados

### DataLookupService

El sistema incluye un servicio de búsqueda y recuperación de datos externos que permite a los agentes enriquecer sus análisis y recomendaciones con información actualizada. Este servicio proporciona las siguientes funcionalidades:

- **Búsqueda de datos de mercado**: Información financiera y económica
- **Búsqueda de noticias**: Artículos y noticias relevantes sobre el tema consultado
- **Búsqueda de informes de industria**: Informes y análisis de sectores específicos
- **Búsqueda web**: Información general desde Internet
- **Información de empresas**: Datos detallados sobre compañías específicas

Estas capacidades permiten a los agentes proporcionar respuestas más completas, actualizadas y basadas en evidencia.

## Métricas y Monitoreo

El sistema incluye un sistema completo de métricas y monitoreo que registra:

- **Tiempos de ejecución de los agentes**
- **Número de solicitudes procesadas**
- **Niveles de confianza de las respuestas**
- **Uso de tokens por modelo**
- **Tasas de error por tipo**

Estas métricas están disponibles en formato Prometheus en el endpoint `/metrics`.

## Desarrollo

### Ejecutar pruebas

```bash
pytest
```

### Añadir un nuevo agente

1. Crear un nuevo archivo en `app/agents/` basado en `base.py`
2. Implementar la lógica especializada en el método `_execute_impl`
3. Registrar el nuevo agente en `app/core/orchestrator.py`
4. Actualizar el `router_agent.py` para incluir el nuevo agente entre las opciones

## Licencia

Este proyecto está licenciado bajo [MIT License](LICENSE).
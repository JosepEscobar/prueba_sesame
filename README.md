# Sistema Multiagente SESAME

Este proyecto contiene un sistema multiagente que utiliza varios servicios especializados para procesar y analizar diferentes tipos de datos empresariales.

## Estructura del proyecto

El proyecto está dividido en tres componentes principales:

- **api_server**: API REST principal que expone los servicios de agentes.
- **mcp_server**: Servidor que proporciona herramientas adicionales para los agentes.
- **frontend**: Interfaz de usuario para interactuar con el sistema.

## Requisitos

- Docker y Docker Compose
- Python 3.12+ (para desarrollo local)
- Node.js 18+ (para desarrollo local del frontend)

## Variables de entorno

Copia el archivo `docker.env.example` a `.env` y configura las variables necesarias:

```bash
cp docker.env.example .env
```

Asegúrate de configurar las siguientes variables:

- `OPENAI_API_KEY`: Clave API de OpenAI
- `OPENAI_MODEL`: Modelo de OpenAI a utilizar (por defecto: gpt-4.1-mini)
- `ALPHA_VANTAGE_API_KEY`: Clave API de Alpha Vantage (para datos financieros)
- `NEWS_API_KEY`: Clave API de News (para noticias)
- `BING_SEARCH_API_KEY`: Clave API de Bing Search (para búsquedas web)

## Ejecución con Docker Compose

Para ejecutar todo el sistema con Docker Compose:

```bash
docker-compose up -d
```

Los servicios estarán disponibles en:

- Frontend: http://localhost:3000
- API Server: http://localhost:8000
- MCP Server: http://localhost:4000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (usuario: admin, contraseña: password)

## Desarrollo local

### API Server

```bash
cd api_server
pip install -r requirements.txt
python -m app.main
```

### MCP Server

```bash
cd mcp_server
pip install -r requirements.txt
python -m app.main
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## Tests

Para ejecutar las pruebas:

```bash
# API Server
cd api_server
pytest

# MCP Server
cd mcp_server
pytest
```

## Monitoreo

El sistema incluye una infraestructura completa de monitorización con Prometheus y Grafana:

### Componentes de monitorización

- **Prometheus**: Recolecta métricas de todos los servicios
  - Disponible en http://localhost:9090
  - Configura el intervalo de scrapping y las reglas de alerta
  - Almacena datos históricos para análisis

- **Grafana**: Proporciona dashboards para visualizar métricas
  - Disponible en http://localhost:3001 (usuario: admin, contraseña: password)
  - Incluye dashboard predefinido "Sesame System Overview"
  - Permite crear dashboards personalizados según necesidades

- **Node-Exporter**: Exporta métricas del sistema operativo
  - Monitoriza CPU, memoria, disco y red
  - Disponible en http://localhost:9100/metrics

- **cAdvisor**: Proporciona métricas de contenedores Docker
  - Monitoriza uso de recursos por contenedor
  - Disponible en http://localhost:8080

### Métricas principales monitorizadas

- **API Server**:
  - Contador de peticiones (`api_server_request_count`)
  - Latencia de respuesta (`api_server_request_latency_seconds`)
  - Consumo de tokens por agente (`api_server_token_count`)
  - Estado del servidor y conexión MCP

- **MCP Server**:
  - Contador de llamadas a herramientas (`mcp_tool_calls_total`)
  - Tiempo de ejecución de herramientas (`mcp_tool_execution_time_seconds`)
  - Contador de errores por herramienta y tipo

- **Sistema**:
  - Uso de CPU, memoria y disco
  - Métricas de red
  - Estado y recursos de contenedores

### Alertas configuradas

El sistema incluye alertas predefinidas para casos como:

- Alto consumo de tokens
- Servidores caídos (API Server o MCP Server)
- Alta latencia en respuestas de API
- Tasas de error elevadas
- Alto uso de recursos del sistema (CPU, memoria, disco)

Para ver y gestionar las alertas:
1. Accede a Prometheus en http://localhost:9090/alerts
2. En Grafana, configura notificaciones en la sección Alerting

### Extendiendo el monitoreo

Para añadir nuevas métricas:

1. Modifica los archivos `api_server/main.py` o `mcp_server/main.py`
2. Añade nuevos contadores, histogramas o gauges con Prometheus
3. Actualiza los dashboards de Grafana para visualizar las nuevas métricas

Para añadir nuevas alertas:
1. Edita el archivo `prometheus/alert_rules.yml`
2. Reinicia los contenedores con `docker-compose restart prometheus`

## CI/CD

El proyecto utiliza GitHub Actions para integración continua y despliegue continuo:

- Pruebas automáticas para cada componente
- Comprobación de estilo y calidad de código
- Generación de imágenes Docker
- Publicación automática de imágenes a GitHub Container Registry
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
docker compose up -d
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

El sistema incluye Prometheus y Grafana para monitoreo:

- Prometheus recoge métricas de todos los servicios
- Grafana proporciona dashboards para visualizar estas métricas

## CI/CD

El proyecto utiliza GitHub Actions para integración continua y despliegue continuo:

- Pruebas automáticas para cada componente
- Comprobación de estilo y calidad de código
- Generación de imágenes Docker
- Publicación automática de imágenes a GitHub Container Registry
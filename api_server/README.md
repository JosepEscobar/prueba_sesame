# API Sesame

Este proyecto implementa el servidor API del sistema Sesame, proporcionando endpoints para interactuar con agentes especializados de asistencia empresarial.

## Características

- Endpoints RESTful para interactuar con agentes de análisis financiero, búsqueda de datos y más
- Integración con servidor MCP para acceso a herramientas externas
- Orquestación de agentes para responder consultas complejas
- Documentación automática de la API

## Requisitos

- Python 3.10 o superior
- Dependencias especificadas en `requirements.txt`

## Instalación

1. Clona este repositorio
2. Crea un entorno virtual
3. Instala las dependencias

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. Crea un archivo `.env` basado en `.env-example` con tus configuraciones

## Uso

Para iniciar el servidor API:

```bash
python main.py
```

La API estará disponible en http://localhost:8000 por defecto.

Para acceder a la documentación de la API, visita:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Estructura del proyecto

```
api_server/
├── app/
│   ├── agents/             # Implementaciones de los agentes especializados
│   ├── api/                # Rutas y modelos de la API
│   ├── core/               # Configuración, logging y funcionalidades centrales
│   ├── services/           # Servicios y conexiones con sistemas externos
│   └── tools/              # Cliente MCP y utilidades
├── logs/                   # Directorio para archivos de log
├── main.py                 # Punto de entrada principal
├── requirements.txt        # Dependencias del proyecto
└── Dockerfile              # Para ejecutar en Docker
```

## Endpoints principales

- `GET /api/health`: Estado de la API
- `POST /api/query`: Enviar una consulta general al sistema
- `POST /api/lookup`: Buscar información específica
- `POST /api/finance`: Obtener análisis financiero

## Integración con el servidor MCP

Esta API se comunica con un servidor MCP para acceder a herramientas externas. El servidor MCP debe estar en ejecución para que algunas funcionalidades estén disponibles.

Configuración de conexión en el archivo `.env`:
```
MCP_CLIENT_URL=http://localhost:4000
```

## Docker

Para ejecutar el servidor en Docker:

```bash
# Construir la imagen
docker build -t api-server .

# Ejecutar el contenedor
docker run -p 8000:8000 api-server
```

## Uso con docker-compose

Para ejecutar como parte de una arquitectura de microservicios:

```yaml
version: '3'
services:
  api_server:
    build: ./api_server
    ports:
      - "8000:8000"
    volumes:
      - ./api_server/logs:/app/logs
    env_file:
      - ./api_server/.env
    depends_on:
      - mcp_server
      
  mcp_server:
    build: ./mcp_server
    ports:
      - "4000:4000"
    volumes:
      - ./mcp_server/logs:/app/logs
    env_file:
      - ./mcp_server/.env
```

## Desarrollo

Para contribuir al proyecto:

1. Crea una rama para tu característica (`git checkout -b feature/amazing-feature`)
2. Realiza tus cambios
3. Ejecuta las pruebas
4. Envía tu pull request 
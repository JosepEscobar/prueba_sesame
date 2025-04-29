# Servidor MCP

Este proyecto implementa un servidor MCP (Model Context Protocol) para proporcionar herramientas mediante una API estandarizada. El servidor MCP permite a diferentes clientes como LangChain, LlamaIndex o agentes personalizados utilizar herramientas locales a través de un protocolo común.

## Características

- Implementación de herramientas financieras y de búsqueda de datos
- Registro dinámico de herramientas desde archivos JSON de esquema
- Métricas de rendimiento y logs completos
- Compatible con implementaciones modernas de FastMCP
- Fácil de extender con nuevas herramientas

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

Para iniciar el servidor MCP:

```bash
python main.py
```

Opciones disponibles:

- `--host`: Host en el que se ejecutará el servidor (por defecto: 0.0.0.0)
- `--port`: Puerto en el que se ejecutará el servidor (por defecto: 4000)

## Estructura del proyecto

```
mcp_server/
├── app/
│   ├── core/
│   │   ├── config.py        # Configuración con pydantic-settings
│   │   ├── logging.py       # Configuración de logs
│   │   └── metrics.py       # Recolector de métricas
│   └── tools/
│       ├── implementations/ # Implementaciones de herramientas
│       ├── schemas/         # Esquemas JSON de herramientas
│       └── server/          # Código del servidor MCP
├── logs/                    # Directorio para archivos de log
├── main.py                  # Punto de entrada principal
├── requirements.txt         # Dependencias del proyecto
└── Dockerfile               # Para ejecutar en Docker
```

## Añadir nuevas herramientas

1. Crea un archivo de esquema JSON en `app/tools/schemas/`
2. Implementa la funcionalidad en `app/tools/implementations/`
3. Registra la implementación en `main.py`

## Docker

Para ejecutar el servidor en Docker:

```bash
# Construir la imagen
docker build -t mcp-server .

# Ejecutar el contenedor
docker run -p 4000:4000 mcp-server
```

## Uso con docker-compose

Para ejecutar como parte de una arquitectura de microservicios:

```yaml
version: '3'
services:
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
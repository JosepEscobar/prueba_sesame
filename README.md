# Proyecto Sesame

Una plataforma de asistencia empresarial que utiliza inteligencia artificial para proporcionar consultoría financiera, análisis de datos y respuestas a consultas empresariales.

## Estructura del proyecto

El proyecto ha sido separado en dos componentes principales:

### 1. Servidor API

Implementa los endpoints RESTful y la lógica de los agentes especializados.

```
api_server/
├── app/
│   ├── agents/         # Implementaciones de los agentes especializados
│   ├── api/            # Rutas y modelos de la API
│   ├── core/           # Configuración, logging y funcionalidades centrales
│   ├── services/       # Servicios y conexiones con sistemas externos
│   └── tools/          # Cliente MCP para consumir herramientas externas
├── logs/               # Directorio para archivos de log
├── main.py             # Punto de entrada principal
└── Dockerfile          # Para ejecutar en Docker
```

### 2. Servidor MCP

Proporciona herramientas mediante el protocolo MCP (Model Context Protocol) para que los agentes puedan acceder a funcionalidades externas.

```
mcp_server/
├── app/
│   ├── core/           # Configuración, logging y métricas
│   └── tools/
│       ├── implementations/ # Implementaciones de herramientas
│       ├── schemas/         # Esquemas JSON de herramientas
│       └── server/          # Código del servidor MCP
├── logs/               # Directorio para archivos de log
├── main.py             # Punto de entrada principal
└── Dockerfile          # Para ejecutar en Docker
```

## Ejecución en desarrollo

Para ejecutar el proyecto en desarrollo, sigue estos pasos:

1. Configura los archivos `.env` en cada directorio basándote en los archivos `.env-example`

2. Inicia el servidor MCP:
```bash
cd mcp_server
python main.py
```

3. En otra terminal, inicia el servidor API:
```bash
cd api_server
python main.py
```

## Ejecución con Docker Compose

El proyecto está configurado para ejecutarse con Docker Compose:

```bash
docker-compose up -d
```

Esto iniciará ambos servicios:
- API: http://localhost:8000
- MCP: http://localhost:4000

## Requisitos

- Python 3.10+
- Dependencias especificadas en los archivos `requirements.txt` de cada componente

## Desarrollo

Para contribuir al proyecto:

1. Clona el repositorio
2. Crea un entorno virtual
3. Instala las dependencias
4. Crea una rama para tu característica (`git checkout -b feature/amazing-feature`)
5. Realiza tus cambios
6. Ejecuta las pruebas
7. Envía tu pull request

## Licencia

Proyecto bajo licencia MIT. Ver archivo `LICENSE` para más detalles.
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

## Configuración del entorno de desarrollo

### Configuración de VS Code

Para configurar VS Code para el desarrollo del proyecto:

1. Instala VS Code desde [https://code.visualstudio.com/](https://code.visualstudio.com/)

2. Instala las siguientes extensiones recomendadas:
   - Python (Microsoft)
   - Ruff (Astral Software)
   - TOML Language Support
   - Pylance
   - Test Explorer UI

3. El proyecto ya incluye una carpeta `.vscode` con la configuración necesaria:
   - `settings.json`: Configuración para Ruff y pytest
   - `launch.json`: Configuraciones para ejecutar y depurar

4. Para ejecutar o depurar:
   - Abre la pestaña "Ejecutar y depurar" (Ctrl+Shift+D o Cmd+Shift+D)
   - Selecciona la configuración deseada en el menú desplegable superior:
     - "API Server": Ejecuta el servidor de API
     - "MCP Server": Ejecuta el servidor MCP
     - "API Server Tests": Ejecuta todas las pruebas del API Server
     - "MCP Server Tests": Ejecuta todas las pruebas del MCP Server
     - "Test File Actual": Ejecuta las pruebas del archivo actual
   - Presiona F5 o el botón verde de ejecutar

5. Para establecer puntos de interrupción (breakpoints):
   - Haz clic en el margen izquierdo junto al número de línea donde deseas detener la ejecución
   - Cuando ejecutes en modo depuración, el programa se detendrá en ese punto
   - Puedes inspeccionar variables, pasar a la siguiente línea, y más usando la barra de herramientas de depuración

### Configuración de pruebas unitarias

Para ejecutar pruebas unitarias desde VS Code:

1. Abre la vista de pruebas en la barra lateral (icono de matraz)
2. VS Code detectará automáticamente las pruebas de pytest de ambos componentes
3. Puedes ejecutar pruebas individuales o todas las pruebas desde esta vista
4. Para depurar una prueba, haz clic derecho en ella y selecciona "Debug Test"

También puedes ejecutar pruebas desde la terminal:
```bash
cd api_server  # o mcp_server
python -m pytest
```

### Configuración de Ruff para formateo y linting

Ruff es un formateador y linter para Python. El proyecto ya incluye un archivo `pyproject.toml` con la configuración necesaria y un `settings.json` que activa Ruff.

1. El formateo y corrección de código se aplicarán automáticamente al guardar los archivos

2. Para formatear manualmente:
   - Abre la paleta de comandos (Ctrl+Shift+P o Cmd+Shift+P)
   - Ejecuta "Ruff: Format Document"

3. Para ver problemas detectados por Ruff:
   - Abre el panel de "Problemas" (Ctrl+Shift+M o Cmd+Shift+M)

## Requisitos

- Python 3.10+
- Dependencias especificadas en los archivos `requirements.txt` de cada componente
- Visual Studio Code (recomendado para desarrollo)

## Desarrollo

Para contribuir al proyecto:

1. Clona el repositorio
2. Crea un entorno virtual
3. Instala las dependencias
4. Crea una rama para tu característica (`git checkout -b feature/amazing-feature`)
5. Realiza tus cambios
6. Ejecuta las pruebas
7. Envía tu pull request

## Configuración de herramientas

El proyecto usa configuración centralizada en `pyproject.toml` para herramientas Python como Ruff, siguiendo las mejores prácticas definidas en PEP 518 y PEP 621.

## Licencia

Proyecto bajo licencia MIT. Ver archivo `LICENSE` para más detalles.
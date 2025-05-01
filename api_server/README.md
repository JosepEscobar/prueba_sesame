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

## Agentes del Sistema

El API Server implementa un sistema multiagente con los siguientes componentes:

### Router Agent
- **Función**: Analiza la consulta del usuario y determina qué agente especializado debe procesarla.
- **Características**:
  - Utiliza análisis semántico para clasificar las consultas.
  - Implementa un sistema de fallback basado en palabras clave.
  - Asigna la consulta al agente más adecuado según su especialidad.

### Guardrail Agent
- **Función**: Verifica que las consultas estén dentro del ámbito permitido por el sistema.
- **Características**:
  - Bloquea consultas potencialmente peligrosas o fuera de alcance.
  - Proporciona respuestas de error amigables cuando una consulta es rechazada.
  - Permite consultas sobre el estado y capacidades del sistema.

### Finance Agent
- **Función**: Gestiona consultas relacionadas con análisis financiero y económico.
- **Características**:
  - Accede a herramientas de análisis financiero a través del servidor MCP.
  - Proporciona análisis de ratios, tendencias y proyecciones.
  - Consulta datos históricos de empresas y mercados.

### Marketing Agent
- **Función**: Atiende consultas sobre estrategias de marketing y análisis de mercado.
- **Características**:
  - Analiza rendimiento de campañas y estrategias de marketing.
  - Genera recomendaciones personalizadas basadas en datos.
  - Accede a herramientas especializadas a través del servidor MCP.

### Analysis Agent
- **Función**: Realiza análisis generales de datos y tendencias que no son específicamente financieros o de marketing.
- **Características**:
  - Procesa series temporales y detecta patrones.
  - Proporciona interpretaciones de datos complejos.
  - Facilita la comprensión de tendencias y correlaciones.

### System Info Agent
- **Función**: Proporciona información sobre el estado y capacidades del sistema.
- **Características**:
  - Responde a consultas sobre las funcionalidades disponibles.
  - Muestra estadísticas del sistema y estado de los servicios.
  - Permite a los usuarios conocer qué agentes están disponibles y sus capacidades.

### Summary Agent
- **Función**: Genera resúmenes concisos de respuestas extensas generadas por otros agentes.
- **Características**:
  - Extrae los puntos clave de respuestas detalladas.
  - Formatea la información de manera clara y concisa.
  - Mejora la experiencia del usuario con respuestas legibles.

## Integración con el servidor MCP

Esta API se comunica con un servidor MCP para acceder a herramientas externas. El servidor MCP debe estar en ejecución para que algunas funcionalidades estén disponibles.

Configuración de conexión en el archivo `.env`:
```
MCP_CLIENT_URL=http://localhost:4000
```

## Flujo de procesamiento de consultas

1. El usuario envía una consulta a `/api/v1/query`.
2. El `GuardrailAgent` verifica si la consulta está dentro del ámbito del sistema.
3. Si es válida, el `RouterAgent` determina qué agente especializado debe manejarla.
4. El agente seleccionado procesa la consulta, utilizando herramientas del MCP si es necesario.
5. Si corresponde, el `SummaryAgent` formatea la respuesta final.
6. La respuesta se devuelve al usuario.

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

## Configuración para desarrollo

### Configuración de VS Code

Para configurar VS Code para el desarrollo del API Server:

1. Abre la carpeta `api_server` en VS Code:
   ```bash
   code ruta/a/proyecto-sesame/api_server
   ```

2. Instala las extensiones recomendadas:
   - Python (Microsoft)
   - Ruff (Astral Software)
   - FastAPI (opcional, para mejor soporte de FastAPI)
   - Test Explorer UI

3. Configuración para depuración:
   - Crea un archivo `.vscode/launch.json` con el siguiente contenido:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "API Server",
         "type": "python",
         "request": "launch",
         "program": "${workspaceFolder}/main.py",
         "console": "integratedTerminal",
         "justMyCode": true
       },
       {
         "name": "Ejecutar Test Actual",
         "type": "python",
         "request": "launch",
         "module": "pytest",
         "args": [
           "${file}"
         ],
         "console": "integratedTerminal"
       },
       {
         "name": "Ejecutar Todos los Tests",
         "type": "python",
         "request": "launch",
         "module": "pytest",
         "console": "integratedTerminal"
       }
     ]
   }
   ```
   - Ahora puedes iniciar la depuración desde VS Code usando F5 o el panel de depuración
   - Para establecer puntos de interrupción, haz clic en el margen izquierdo junto al número de línea
   - La depuración te permitirá inspeccionar variables, seguir la ejecución paso a paso y evaluar expresiones

### Ejecutar pruebas unitarias

Para ejecutar las pruebas unitarias desde VS Code:

1. Abre la vista de pruebas en la barra lateral (icono de matraz)
2. VS Code detectará automáticamente las pruebas de pytest
3. Puedes ejecutar pruebas individuales o todas las pruebas desde esta vista
4. Para depurar una prueba específica, haz clic derecho en ella y selecciona "Debug Test"

También puedes ejecutar pruebas desde la terminal:
```bash
python -m pytest
```

### Formateo de código con Ruff

El proyecto utiliza Ruff como linter y formateador de código. Configúralo en tu entorno:

1. Instala la extensión de Ruff para VS Code:
   - Abre VS Code
   - Presiona `Ctrl+P` (o `Cmd+P` en macOS)
   - Pega el siguiente comando: `ext install charliermarsh.ruff`

2. Asegúrate de tener Ruff instalado: `pip install ruff`

3. Configura VS Code para usar Ruff automáticamente:
   - Abre la paleta de comandos con `Ctrl+Shift+P` o `Cmd+Shift+P`
   - Busca "Preferences: Open Settings (JSON)"
   - Añade lo siguiente:
   ```json
   {
     "editor.formatOnSave": true,
     "editor.codeActionsOnSave": {
       "source.fixAll.ruff": true,
       "source.organizeImports.ruff": true
     },
     "[python]": {
       "editor.defaultFormatter": "charliermarsh.ruff"
     }
   }
   ```

4. El formateo y corrección de código se aplicarán automáticamente al guardar los archivos
5. Para formatear manualmente un archivo, abre la paleta de comandos y ejecuta "Ruff: Format Document"
6. Para ver problemas detectados por Ruff, abre el panel de "Problemas" (Ctrl+Shift+M o Cmd+Shift+M) 
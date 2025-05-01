# Servidor MCP para Sesame

Este proyecto implementa un servidor [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) que expone herramientas de análisis financiero, marketing y datos a modelos de lenguaje como Claude, GPT y otros agentes compatibles con MCP.

## Descripción

El servidor MCP proporciona una serie de herramientas especializadas para análisis financiero, marketing y procesamiento de datos, permitiendo a los modelos de lenguaje realizar operaciones específicas de dominio sin necesidad de acceso a internet o APIs externas.

## Características

- 📊 **Herramientas financieras**: Búsqueda de datos financieros y cálculo de ratios
- 📈 **Herramientas de marketing**: Análisis de campañas y recomendaciones estratégicas
- 📉 **Herramientas de análisis de datos**: Detección de tendencias y predicciones simples

## Requisitos

- Python 3.9+
- Paquetes Python según `requirements.txt`

## Instalación

1. Clonar este repositorio
2. Instalar dependencias:

```bash
cd mcp_server
pip install -r requirements.txt
```

## Uso

### Iniciar el servidor

Para iniciar el servidor MCP:

```bash
python main.py
```

El servidor se iniciará en `http://localhost:4000` utilizando el transporte SSE (Server-Sent Events).

### Integración con agentes Sesame

Los agentes de Sesame en el `api_server` están diseñados para conectarse con este servidor MCP siguiendo el patrón de integración oficial de MCP con LangChain y LangGraph.

```python
# Configuración del cliente MCP siguiendo el patrón oficial
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

# Configurar cliente MCP
client = MultiServerMCPClient({
    "sesame": {
        "transport": "sse",
        "url": "http://localhost:4000",
    }
})

# Cargar herramientas MCP adaptadas a LangChain
tools = load_mcp_tools(client)

# Luego usar esas herramientas con tu agente LangChain
# agent = Agent(..., tools=tools)
```

Para que los agentes puedan acceder a las herramientas MCP, asegúrate de:

1. Iniciar primero el servidor MCP: `python mcp_server/main.py`
2. Configurar la URL correcta en el archivo `.env` del `api_server`:
   ```
   MCP_CLIENT_URL=http://localhost:4000
   ```

Los agentes finance_agent y marketing_agent invocan automáticamente herramientas externas como `analizar_tendencia`, `recomendar_estrategia_marketing` y `calcular_ratios_financieros` cuando es apropiado.

### Conectar con Claude

Para usar este servidor con Claude, puedes especificar la siguiente configuración en la API de Claude:

```json
{
  "mcpServers": {
    "sesame": {
      "url": "http://localhost:4000/sse",
      "transport": "sse"
    }
  }
}
```

### Usar con LangGraph

Para usar este servidor con LangGraph, siguiendo el patrón oficial:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o")

# Configure the client with the servers
client = MultiServerMCPClient(
    {
        "sesame": {
            "transport": "sse",
            "url": "http://localhost:4000",
        }
    }
)

# Load the tools from the client
tools = load_mcp_tools(client)

# Create a REACT agent with the model and tools
agent = create_react_agent(model, tools)

# Invoke the agent
response = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "Analiza los datos financieros de Apple"}]}
)
```

## Herramientas disponibles

### Análisis financiero

- `buscar_datos_financieros`: Obtiene datos financieros de una empresa
- `calcular_ratios_financieros`: Calcula ratios financieros a partir de datos básicos

### Marketing

- `analizar_rendimiento_campania`: Analiza el rendimiento de una campaña de marketing
- `recomendar_estrategia_marketing`: Recomienda estrategias basadas en parámetros básicos

### Análisis de datos

- `analizar_tendencia`: Analiza una serie temporal y detecta tendencias
- `predecir_valores`: Realiza una predicción simple de valores futuros

## Desarrollo

Para contribuir a este proyecto:

1. Crea un entorno virtual de Python
2. Instala las dependencias de desarrollo: `pip install -r requirements.txt`
3. Ejecuta pruebas: `pytest`

## Configuración para desarrollo

### Configuración de VS Code

Para configurar VS Code para el desarrollo del servidor MCP:

1. Abre la carpeta `mcp_server` en VS Code:
   ```bash
   code ruta/a/proyecto-sesame/mcp_server
   ```

2. Instala las extensiones recomendadas:
   - Python (Microsoft)
   - Ruff (Astral Software)
   - TOML Language Support
   - Test Explorer UI

3. Configuración para depuración:
   - Crea un archivo `.vscode/launch.json` con el siguiente contenido:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "MCP Server",
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
   - Puedes ejecutar el servidor normalmente o iniciar cualquiera de las configuraciones de prueba

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

## Recursos adicionales

- [Documentación de Model Context Protocol](https://modelcontextprotocol.io/)
- [Adaptadores MCP para LangChain](https://github.com/langchain-ai/langchain-mcp-adapters)
- [LangGraph con MCP](https://langchain-ai.github.io/langgraph/agents/mcp/) 
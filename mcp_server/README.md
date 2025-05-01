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

## Recursos adicionales

- [Documentación de Model Context Protocol](https://modelcontextprotocol.io/)
- [Adaptadores MCP para LangChain](https://github.com/langchain-ai/langchain-mcp-adapters)
- [LangGraph con MCP](https://langchain-ai.github.io/langgraph/agents/mcp/) 
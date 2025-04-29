# Servidor MCP para herramientas locales

Este módulo proporciona una implementación de servidor MCP (Model Context Protocol) para exponer herramientas locales siguiendo el estándar oficial de MCP.

## Características

- **Integración con el Protocolo MCP**: Implementación completa compatible con el estándar [MCP](https://modelcontextprotocol.io/).
- **Exposición de herramientas locales**: Permite exponer herramientas locales como APIs MCP.
- **Gestión automática de errores**: Manejo centralizado de errores, logging y métricas.
- **Carga dinámica de esquemas**: Carga esquemas de herramientas desde archivos JSON.

## Uso básico

### Iniciar el servidor MCP

El servidor MCP se inicia automáticamente con la aplicación principal. Sin embargo, también puede ejecutarse de forma independiente:

```python
import asyncio
from app.tools.server.server_init import init_mcp_server, run_server

async def main():
    # Inicializar el servidor
    server = await init_mcp_server(host="localhost", port=4000)
    
    # Ejecutar el servidor
    await run_server(server)

if __name__ == "__main__":
    asyncio.run(main())
```

### Registrar herramientas

El servidor carga automáticamente los esquemas de herramientas desde el directorio `app/tools/schemas/`. Para registrar una nueva herramienta:

1. Cree un archivo JSON con el esquema de la herramienta en `app/tools/schemas/`.
2. Implemente la herramienta en `app/tools/implementations/`.
3. Registre la implementación en `app/tools/server/server_init.py`.

## Integración con LangChain

Este servidor MCP es compatible con el adaptador de LangChain:

```python
from langchain_mcp.adapters import MCPClient

client = MCPClient(base_url="http://localhost:4000")
tools = await client.list_tools()
```

## Estructura de directorios

```
app/tools/
├── schemas/                # Esquemas JSON de herramientas
├── implementations/        # Implementaciones de herramientas
├── server/                 # Servidor MCP
│   ├── mcp_server.py       # Clase principal del servidor
│   ├── server_init.py      # Script de inicialización
│   └── financial_models_impl.py  # Implementación de ejemplo
└── mcp_client_official.py  # Cliente MCP oficial
```

## Herramientas disponibles

- **financial_models**: Proporciona modelos financieros para diferentes escenarios empresariales.
- **query_kb**: Consulta una base de conocimiento interna.
- **search_articles**: Busca artículos académicos.

## Desarrollo de nuevas herramientas

Para agregar una nueva herramienta al servidor MCP:

1. **Definir el esquema**: Cree un archivo JSON en `app/tools/schemas/` con la definición de la herramienta.
2. **Implementar la herramienta**: Cree una clase en `app/tools/implementations/` que proporcione la funcionalidad.
3. **Registrar la herramienta**: Agregue la herramienta en `app/tools/server/server_init.py`.

Ejemplo de esquema JSON:

```json
{
    "name": "mi_herramienta",
    "description": "Descripción de la herramienta",
    "inputs": {
        "type": "object",
        "properties": {
            "parametro1": {
                "type": "string",
                "description": "Descripción del parámetro"
            }
        },
        "required": ["parametro1"]
    },
    "outputs": {
        "type": "object",
        "properties": {
            "resultado": {
                "type": "string",
                "description": "Descripción del resultado"
            }
        }
    }
}
```

## Referencias

- [Especificación MCP](https://modelcontextprotocol.io/introduction)
- [Adaptadores LangChain MCP](https://github.com/langchain-ai/langchain-mcp-adapters)
- [MCP Server Quickstart](https://modelcontextprotocol.io/quickstart/server)
- [MCP Client Quickstart](https://modelcontextprotocol.io/quickstart/client) 
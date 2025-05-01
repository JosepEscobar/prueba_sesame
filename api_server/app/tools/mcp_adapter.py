from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from app.core.config import get_settings


# Inicializar cliente MCP HTTP/SSE usando LangChain adapters
def get_mcp_tools():
    """
    Obtiene las herramientas MCP adaptadas para LangChain/LangGraph
    siguiendo el patrón oficial de la documentación.
    
    Returns:
        Lista de herramientas adaptadas para LangChain
    """
    settings = get_settings()

    # Configurar cliente según la documentación oficial
    client = MultiServerMCPClient({
        "sesame": {  # Nombre del servidor
            "transport": "sse",
            "url": settings.MCP_CLIENT_URL,
        }
        # Se pueden configurar múltiples servidores si es necesario
        # "filesystem": {
        #     "command": "npx",
        #     "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
        # },
        # "postgres": {
        #     "command": "npx",
        #     "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/mydb"]
        # }
    })

    # Cargar herramientas MCP adaptadas a LangChain
    return load_mcp_tools(client)

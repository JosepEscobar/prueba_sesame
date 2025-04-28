from typing import Dict, Any, List, Optional
import json
import aiohttp
import logging
from app.core.logging import logger

class MCPClient:
    """
    Cliente para interactuar con servidores MCP (Model Context Protocol).
    Permite a los agentes acceder a herramientas externas de forma estandarizada.
    """
    
    def __init__(self, base_url: str = "http://localhost:4000/mcp"):
        """
        Inicializa el cliente MCP.
        
        Args:
            base_url: URL base del servidor MCP
        """
        self.base_url = base_url
        self.tools_cache: Optional[List[Dict[str, Any]]] = None
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self):
        """Asegura que la sesión HTTP está inicializada."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Cierra la sesión HTTP."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        Lista las herramientas disponibles en el servidor MCP.
        
        Returns:
            Lista de herramientas disponibles
        """
        # En una implementación real, esto haría una solicitud al servidor MCP
        # Por ahora, simulamos la respuesta
        
        # Si ya tenemos las herramientas en caché, las devolvemos
        if self.tools_cache:
            return self.tools_cache
        
        try:
            # Simular herramientas disponibles
            self.tools_cache = [
                {
                    "name": "search_articles",
                    "description": "Busca artículos académicos dada una consulta de búsqueda.",
                    "inputs": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Términos de búsqueda"},
                            "max_results": {"type": "integer", "description": "Número máximo de resultados", "default": 5}
                        },
                        "required": ["query"]
                    },
                    "outputs": {
                        "type": "object",
                        "properties": {
                            "articles": {"type": "array", "items": {"type": "object"}}
                        }
                    }
                },
                {
                    "name": "query_kb",
                    "description": "Consulta la base de conocimiento interna.",
                    "inputs": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Términos de búsqueda"},
                            "kb_name": {"type": "string", "description": "Nombre de la base de conocimiento"}
                        },
                        "required": ["query"]
                    },
                    "outputs": {
                        "type": "object",
                        "properties": {
                            "results": {"type": "array", "items": {"type": "object"}}
                        }
                    }
                },
                {
                    "name": "financial_models",
                    "description": "Obtiene modelos o plantillas financieras.",
                    "inputs": {
                        "type": "object",
                        "properties": {
                            "model_type": {"type": "string", "description": "Tipo de modelo financiero"},
                            "industry": {"type": "string", "description": "Industria específica", "default": "general"}
                        },
                        "required": ["model_type"]
                    },
                    "outputs": {
                        "type": "object",
                        "properties": {
                            "models": {"type": "array", "items": {"type": "object"}}
                        }
                    }
                }
            ]
            
            logger.info(f"Herramientas MCP cargadas: {len(self.tools_cache)}")
            return self.tools_cache
            
        except Exception as e:
            logger.error(f"Error al listar herramientas MCP: {str(e)}")
            return []
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Llama a una herramienta específica en el servidor MCP.
        
        Args:
            tool_name: Nombre de la herramienta a llamar
            params: Parámetros para la herramienta
            
        Returns:
            Resultado de la llamada a la herramienta
        """
        # En una implementación real, esto haría una solicitud al servidor MCP
        # Por ahora, simulamos la respuesta
        
        # Verificar que la herramienta existe
        tools = await self.list_tools()
        tool_exists = any(tool["name"] == tool_name for tool in tools)
        
        if not tool_exists:
            logger.error(f"Herramienta no encontrada: {tool_name}")
            return {"error": f"Herramienta no encontrada: {tool_name}"}
        
        try:
            # Simular llamada a la herramienta
            logger.info(f"Llamando a herramienta MCP: {tool_name}")
            
            # Generar una respuesta simulada según la herramienta
            if tool_name == "search_articles":
                query = params.get("query", "")
                max_results = params.get("max_results", 5)
                
                # Simulación de búsqueda de artículos
                articles = []
                for i in range(min(3, max_results)):
                    articles.append({
                        "title": f"Artículo sobre {query} #{i+1}",
                        "authors": ["Autor Ejemplo"],
                        "publication": "Revista de Ejemplo",
                        "year": 2023,
                        "summary": f"Este es un resumen del artículo sobre {query}.",
                        "url": f"https://example.com/articles/{i+1}"
                    })
                
                return {"articles": articles}
                
            elif tool_name == "query_kb":
                query = params.get("query", "")
                kb_name = params.get("kb_name", "general")
                
                # Simulación de consulta a la base de conocimiento
                results = []
                for i in range(2):
                    results.append({
                        "title": f"Documento sobre {query} en {kb_name}",
                        "content": f"Este es el contenido del documento sobre {query} en la base de conocimiento {kb_name}.",
                        "relevance": 0.95 - (i * 0.1),
                        "last_updated": "2023-08-15"
                    })
                
                return {"results": results}
                
            elif tool_name == "financial_models":
                model_type = params.get("model_type", "")
                industry = params.get("industry", "general")
                
                # Simulación de obtención de modelos financieros
                models = []
                for i in range(2):
                    models.append({
                        "name": f"Modelo {model_type} para {industry} #{i+1}",
                        "description": f"Este es un modelo financiero de tipo {model_type} para la industria {industry}.",
                        "format": "Excel",
                        "download_url": f"https://example.com/financial_models/{model_type}_{industry}_{i+1}.xlsx"
                    })
                
                return {"models": models}
            
            else:
                return {"error": "Implementación de herramienta no disponible"}
                
        except Exception as e:
            logger.error(f"Error al llamar a herramienta MCP {tool_name}: {str(e)}")
            return {"error": f"Error en la llamada a la herramienta: {str(e)}"}
    
    def __del__(self):
        """Asegura que la sesión se cierre al eliminar el objeto."""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.session.close())
                else:
                    loop.run_until_complete(self.session.close())
            except Exception:
                pass  # Ignorar errores al cerrar la sesión 
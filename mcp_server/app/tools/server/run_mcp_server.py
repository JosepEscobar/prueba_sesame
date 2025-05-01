
import asyncio
import signal
import sys

# Añadir el directorio raíz al path de Python
sys.path.insert(0, "/Users/josepescobar/Developer/prueba_sesame")

from app.core.logging import logger, setup_logging
from app.tools.server.server_init import init_mcp_server, run_server

# Configurar logging
setup_logging()

# Manejador de señales para cerrar limpiamente
def handle_signal(signum, frame):
    logger.info(f"Recibida señal {signum}, cerrando servidor MCP...")
    sys.exit(0)

# Registrar manejadores de señales
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

async def main():
    try:
        logger.info("Iniciando servidor MCP en proceso separado...")
        # Inicializar el servidor
        server = await init_mcp_server(host="localhost", port=4000)

        # Ejecutar el servidor (esta función es bloqueante)
        await run_server(server)
    except Exception as e:
        logger.error(f"Error al ejecutar servidor MCP: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Proceso del servidor MCP interrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error en proceso del servidor MCP: {str(e)}")
        sys.exit(1)

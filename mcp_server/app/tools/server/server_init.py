import argparse
import asyncio
import atexit
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from app.core.logging import logger
from app.tools.server.mcp_server import MCPToolServer, run_server

# Variable global para almacenar el proceso del servidor MCP
_mcp_process: subprocess.Popen | None = None

def init_mcp_server(host: str = "localhost", port: int = 4000) -> MCPToolServer:
    """
    Inicializa el servidor MCP (para uso dentro del mismo proceso).
    Esta función se mantiene por compatibilidad pero ya no se recomienda su uso.
    
    Args:
        host: Host donde se iniciará el servidor MCP
        port: Puerto donde se iniciará el servidor MCP
        
    Returns:
        Una instancia de MCPToolServer inicializada
    """
    logger.warning("Usar init_mcp_server está obsoleto. Se recomienda usar start_mcp_server_process para ejecutar el servidor en un proceso separado.")
    return MCPToolServer(host=host, port=port)

def stop_mcp_server_process() -> bool:
    """
    Detiene el proceso del servidor MCP si está en ejecución.
    
    Returns:
        True si el servidor se detuvo correctamente, False en caso contrario
    """
    global _mcp_process

    if _mcp_process is None:
        # No hay proceso para detener
        return True

    try:
        # Verificar si el proceso aún está en ejecución
        if _mcp_process.poll() is None:
            logger.info(f"Deteniendo proceso del servidor MCP (PID: {_mcp_process.pid})")

            # Intentar terminar el proceso de forma limpia
            try:
                os.killpg(os.getpgid(_mcp_process.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError) as e:
                logger.warning(f"No se pudo enviar SIGTERM al proceso: {str(e)}")
                # Intentar terminar directamente el proceso
                _mcp_process.terminate()

            # Esperar a que el proceso termine
            try:
                _mcp_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Si sigue sin terminar, forzar la terminación
                logger.warning("El proceso no respondió a SIGTERM, enviando SIGKILL")
                try:
                    os.killpg(os.getpgid(_mcp_process.pid), signal.SIGKILL)
                except (ProcessLookupError, PermissionError, OSError):
                    _mcp_process.kill()

                # Esperar nuevamente
                try:
                    _mcp_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    logger.error("No se pudo terminar el proceso del servidor MCP")
                    return False

        # Limpiar el archivo temporal si existe
        if hasattr(_mcp_process, 'script_path') and os.path.exists(_mcp_process.script_path):
            try:
                os.unlink(_mcp_process.script_path)
                logger.debug(f"Eliminado script temporal: {_mcp_process.script_path}")
            except OSError as e:
                logger.warning(f"No se pudo eliminar el script temporal: {str(e)}")

        # Limpiar archivo de bandera si existe
        ready_file = Path(__file__).parent.parent.parent.parent / "mcp_server_ready.flag"
        if os.path.exists(ready_file):
            try:
                os.unlink(ready_file)
                logger.debug("Eliminado archivo de bandera del servidor MCP")
            except OSError as e:
                logger.warning(f"No se pudo eliminar archivo de bandera: {str(e)}")

        # Limpiar la referencia global
        _mcp_process = None
        logger.info("Proceso del servidor MCP detenido correctamente")
        return True

    except Exception as e:
        logger.error(f"Error al detener el proceso del servidor MCP: {str(e)}")
        # Limpiar la referencia global en caso de error
        _mcp_process = None
        return False

def start_mcp_server_process(host: str = "localhost", port: int = 4000) -> subprocess.Popen | None:
    """
    Inicia el servidor MCP en un proceso separado.
    
    Args:
        host: Host donde se iniciará el servidor MCP
        port: Puerto donde se iniciará el servidor MCP
        
    Returns:
        El proceso de Popen si el servidor se inició correctamente, None en caso contrario
    """
    global _mcp_process

    # Detener cualquier servidor MCP existente
    stop_mcp_server_process()

    # Crear un script temporal para ejecutar el servidor MCP
    try:
        # Crear un archivo temporal que ejecutará el servidor MCP
        fd, script_path = tempfile.mkstemp(suffix='.py', prefix='mcp_server_')
        logger.debug(f"Creando script temporal en {script_path}")

        # Obtener la ruta del proyecto para importaciones correctas
        project_root = Path(__file__).parent.parent.parent.parent

        # Escribir el contenido del script
        with os.fdopen(fd, 'w') as f:
            f.write(f"""
import os
import sys
import signal
import time
import logging
import asyncio
import json
import socket
from pathlib import Path

# Añadir el directorio raíz del proyecto al path para importaciones
sys.path.insert(0, "{project_root}")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("{project_root / 'logs' / 'mcp_server.log'}")
    ]
)
logger = logging.getLogger("mcp_server")
logger.info("Iniciando proceso separado para servidor MCP")

# Variables para rastrear si el servidor está en ejecución
server_running = False
server_ready = False

# Verificar si el puerto ya está en uso
def check_port_in_use(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("localhost", port))
        s.close()
        return False
    except socket.error:
        return True

# Si el puerto ya está en uso, salir
if check_port_in_use({port}):
    logger.error(f"El puerto {port} ya está en uso. No se puede iniciar el servidor MCP.")
    sys.exit(1)

# Manejar señales para cerrar correctamente
def handle_signal(signum, frame):
    logger.info(f"Señal recibida: {{signum}}, deteniendo servidor MCP")
    global server_running
    if server_running:
        # Flag para detener el servidor
        server_running = False
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

# Importar el servidor MCP
from mcp.server.fastmcp import FastMCP
from app.tools.server.mcp_server import MCPToolServer

# Función principal
async def main():
    global server_running, server_ready
    
    try:
        # Crear instancia del servidor
        server = MCPToolServer(host="{host}", port={port})
        
        # Cargar las herramientas (desde los archivos JSON)
        tool_schemas_dir = Path("{project_root / 'app' / 'tools' / 'schemas'}")
        loaded_tools = 0
        
        if not tool_schemas_dir.exists():
            logger.error(f"Directorio de esquemas no encontrado: {{tool_schemas_dir}}")
            return False
            
        json_files = list(tool_schemas_dir.glob("*.json"))
        if not json_files:
            logger.error(f"No se encontraron archivos JSON en {{tool_schemas_dir}}")
            logger.info(f"Contenido del directorio: {{[f.name for f in tool_schemas_dir.iterdir()]}}")
            return False
        
        # Cargar todas las herramientas disponibles
        for json_file in json_files:
            try:
                logger.info(f"Cargando herramienta '{{json_file.stem}}' desde {{json_file.name}}")
                
                # Verificar que el archivo sea un JSON válido
                try:
                    with open(json_file, 'r') as schema_file:
                        schema_data = json.load(schema_file)
                    # Verificar que tenga los campos necesarios
                    if "name" not in schema_data or "description" not in schema_data:
                        logger.error(f"Esquema inválido en {{json_file}}: faltan campos obligatorios")
                        continue
                except json.JSONDecodeError:
                    logger.error(f"El archivo {{json_file}} no es un JSON válido")
                    continue
                    
                # Registrar la herramienta
                success = await server.register_tool_from_json(json_file)
                if success:
                    loaded_tools += 1
                    logger.info(f"Herramienta '{{json_file.stem}}' cargada correctamente")
                else:
                    logger.warning(f"No se pudo cargar la herramienta desde {{json_file}}")
            except Exception as e:
                logger.error(f"Error al cargar herramienta desde {{json_file}}: {{str(e)}}", exc_info=True)
        
        if loaded_tools == 0:
            logger.error("No se pudo cargar ninguna herramienta. Verificar los archivos de esquema.")
            return False
            
        logger.info(f"Cargadas {{loaded_tools}} herramientas")
        
        # Registrar implementaciones específicas
        try:
            # Registrar implementación de financial_models
            from app.tools.implementations.financial_models import FinancialModelsImplementation
            financial_models_impl = FinancialModelsImplementation()
            
            success = server.register_tool_implementation(
                "financial_models", 
                financial_models_impl.execute
            )
            
            if success:
                logger.info("Implementación de financial_models registrada correctamente")
            else:
                logger.warning("No se pudo registrar la implementación de financial_models")
                
            # Registrar implementación de data_lookup
            from app.tools.implementations.data_lookup import DataLookupImplementation
            data_lookup_impl = DataLookupImplementation()
            
            success = server.register_tool_implementation(
                "data_lookup", 
                data_lookup_impl.execute
            )
            
            if success:
                logger.info("Implementación de data_lookup registrada correctamente")
            else:
                logger.warning("No se pudo registrar la implementación de data_lookup")
        except Exception as e:
            logger.error(f"Error al registrar implementaciones: {{str(e)}}", exc_info=True)
        
        # Configurar el servidor MCP antes de iniciarlo
        server.mcp_server.server_host = "{host}"
        server.mcp_server.server_port = {port}
        
        # Iniciar el servidor directamente (no a través de start_server)
        logger.info("Iniciando servidor MCP...")
        
        # Iniciar el servidor MCP directamente
        # Crear y ejecutar el servidor
        server_task = asyncio.create_task(server.mcp_server.run())
        server._is_running = True
        
        # Marcar que el servidor está listo
        server_running = True
        server_ready = True
        
        logger.info(f"Servidor MCP iniciado en http://{host}:{port}")
        
        # Escribir un archivo indicador para señalar que estamos listos
        ready_file = Path("{project_root}/mcp_server_ready.flag")
        with open(ready_file, 'w') as f:
            f.write(f"Servidor MCP listo en {{time.time()}}")
        
        logger.info(f"Servidor MCP escuchando y listo para recibir solicitudes")
        
        # Mantener el servidor en ejecución
        while server_running:
            await asyncio.sleep(1)
            
        # Limpiar y detener el servidor al salir del bucle
        if os.path.exists(ready_file):
            os.unlink(ready_file)
            
        logger.info("Deteniendo servidor MCP...")
        server_task.cancel()
        server._is_running = False
        logger.info("Servidor MCP detenido correctamente")
        
        return True
    except Exception as e:
        logger.error(f"Error en el servidor MCP: {{str(e)}}", exc_info=True)
        return False

if __name__ == "__main__":
    # Ejecutar el bucle de eventos
    try:
        # Ejecutar la función principal y esperar a que esté listo
        result = asyncio.run(main())
        
        # Si hubo un error al inicializar, salir
        if not result:
            logger.error("No se pudo inicializar el servidor MCP")
            sys.exit(1)
            
        # Si llegamos aquí, el servidor se inició correctamente
        # Mantener el proceso en ejecución
        logger.info("Servidor MCP iniciado correctamente, manteniendo proceso")
        
        # Esto mantiene el proceso activo hasta que se reciba una señal
        while server_running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Proceso interrumpido por teclado")
    except Exception as e:
        logger.error(f"Error fatal en el servidor MCP: {{str(e)}}", exc_info=True)
    finally:
        server_running = False
        logger.info("Finalizando proceso del servidor MCP")
        sys.exit(0)
""")

        # Ejecutar el script en un proceso separado
        logger.info(f"Iniciando proceso separado para el servidor MCP en {host}:{port}")

        # Construir el comando
        python_executable = sys.executable

        # Iniciar el proceso
        process = subprocess.Popen(
            [python_executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            # No redirigir stdin para evitar bloqueos
            stdin=subprocess.DEVNULL,
            # Desacoplar el proceso para que sea independiente
            start_new_session=True
        )

        # Almacenar el proceso y el path del script
        _mcp_process = process
        _mcp_process.script_path = script_path  # Guardar el path para eliminarlo después

        # Registrar el método de limpieza
        atexit.register(stop_mcp_server_process)

        # Verificar si el proceso inició correctamente (esperar un poco)
        time.sleep(2.0)  # Esperar más tiempo para que el proceso arranque completamente

        # Verificar si el proceso sigue en ejecución
        if process.poll() is not None:
            # El proceso terminó inmediatamente, algo salió mal
            stdout, stderr = process.communicate()
            logger.error(f"Error al iniciar el servidor MCP en proceso separado: {stderr}")

            # Limpiar
            if os.path.exists(script_path):
                os.unlink(script_path)

            return None

        # Verificar si el servidor está respondiendo
        # Intentar varias veces con un breve retraso
        max_retries = 10
        retry_delay = 0.5
        server_up = False

        # Archivo indicador que el servidor MCP crea cuando está listo
        ready_file = Path(project_root) / "mcp_server_ready.flag"

        for attempt in range(max_retries):
            if os.path.exists(ready_file):
                try:
                    with open(ready_file) as f:
                        flag_content = f.read()
                    logger.info(f"Servidor MCP listo: {flag_content}")
                    server_up = True
                    break
                except Exception as e:
                    logger.warning(f"Error al leer archivo indicador: {str(e)}")

            logger.info(f"Esperando a que el servidor MCP esté listo (intento {attempt+1}/{max_retries})")
            time.sleep(retry_delay)

        if not server_up:
            logger.error("El servidor MCP no está respondiendo después de varios intentos")
            # Leer la salida del proceso para diagnóstico
            stdout, stderr = process.communicate()
            if stdout:
                logger.info(f"Salida del servidor: {stdout}")
            if stderr:
                logger.error(f"Error del servidor: {stderr}")

            # Intentar detener el proceso
            stop_mcp_server_process()
            return None

        logger.info(f"Proceso del servidor MCP iniciado con PID {process.pid}")
        return process

    except Exception as e:
        logger.error(f"Error al iniciar el servidor MCP en proceso separado: {str(e)}")

        # Limpiar si algo sale mal
        if 'script_path' in locals() and os.path.exists(script_path):
            os.unlink(script_path)

        return None

async def init_mcp_server(host: str = "localhost", port: int = 4000) -> MCPToolServer:
    """
    Inicializa y configura un servidor MCP con las herramientas disponibles.
    
    Args:
        host: Host en el que se ejecutará el servidor
        port: Puerto en el que se ejecutará el servidor
        
    Returns:
        Instancia del servidor MCP configurado
    """
    # Crear el servidor MCP
    server = MCPToolServer(host=host, port=port)

    # Cargar esquemas desde el directorio de esquemas
    schemas_dir = Path(__file__).parent.parent / "schemas"
    server.register_tools_from_directory(schemas_dir)

    # Registrar implementación de financial_models
    try:
        from app.tools.implementations.financial_models import (
            FinancialModelsImplementation,
        )
        financial_models_impl = FinancialModelsImplementation()

        server.register_tool_implementation(
            "financial_models",
            financial_models_impl.execute
        )
        logger.info("Implementación de financial_models registrada correctamente")
    except Exception as e:
        logger.error(f"Error al registrar implementación de financial_models: {str(e)}")

    # Agregar implementaciones para otras herramientas aquí

    return server

async def main():
    """Punto de entrada principal para iniciar el servidor MCP."""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Servidor MCP para herramientas locales")
    parser.add_argument("--host", default="localhost", help="Host para el servidor MCP")
    parser.add_argument("--port", type=int, default=4000, help="Puerto para el servidor MCP")
    args = parser.parse_args()

    # Inicializar el servidor
    server = await init_mcp_server(host=args.host, port=args.port)

    # Ejecutar el servidor
    await run_server(server)

if __name__ == "__main__":
    # Ejecutar el bucle de eventos
    asyncio.run(main())

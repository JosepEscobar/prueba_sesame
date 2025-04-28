# Sistema Multi-Agente con LangGraph y FastAPI

Este proyecto implementa un sistema multi-agente utilizando LangGraph para orquestar la interacción entre diferentes agentes especializados. El sistema está diseñado para procesar solicitudes de usuarios y dirigirlas al agente más adecuado para manejarlas.

## Características

- Sistema de orquestación basado en LangGraph
- Agentes especializados: Análisis, Acción y Resumen
- Router inteligente para determinar el agente adecuado para cada solicitud
- Logging estructurado en formato JSON
- Sistema de métricas con Prometheus
- API RESTful con FastAPI
- Contenedores Docker para despliegue

## Estructura del Proyecto

```
├── app/
│   ├── agents/                  # Agentes especializados
│   │   ├── base.py              # Clase base para agentes
│   │   ├── router_agent.py      # Agente de enrutamiento
│   │   ├── analysis_agent.py    # Agente de análisis
│   │   ├── action_agent.py      # Agente de acción
│   │   └── summary_agent.py     # Agente de resumen
│   ├── api/                     # Endpoints de API
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── agents.py    # Endpoints para los agentes
│   │       └── router.py        # Router principal de la API
│   ├── core/                    # Funcionalidades centrales
│   │   ├── config.py            # Configuración
│   │   ├── logging.py           # Sistema de logging
│   │   ├── metrics.py           # Sistema de métricas
│   │   └── orchestrator.py      # Orquestador de agentes
│   └── main.py                  # Punto de entrada de la aplicación
├── examples/                    # Ejemplos de uso
│   └── run_examples.py          # Script para ejecutar ejemplos
├── tests/                       # Tests automatizados
│   └── test_orchestrator.py     # Tests para el orquestador
├── .env.example                 # Plantilla para variables de entorno
├── Dockerfile                   # Docker para despliegue
├── docker-compose.yml           # Composición Docker
├── requirements.txt             # Dependencias
└── README.md                    # Este archivo
```

## Requisitos

- Python 3.10+
- OpenAI API Key
- Docker (opcional, para despliegue)

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/tuusuario/sistema-multi-agente.git
   cd sistema-multi-agente
   ```

2. Crear un entorno virtual y activarlo:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   # Editar .env con tu API key de OpenAI y otras configuraciones
   ```

## Uso

### Ejecutar la API

```bash
uvicorn app.main:app --reload
```

La API estará disponible en http://localhost:8000. La documentación de la API se puede acceder en http://localhost:8000/docs.

### Ejecutar Ejemplos

```bash
# Listar ejemplos disponibles
python examples/run_examples.py --list

# Ejecutar un ejemplo específico
python examples/run_examples.py --type analysis

# Ejecutar un ejemplo personalizado
python examples/run_examples.py --type custom
```

### Endpoints Principales

- `POST /api/v1/process`: Procesa una solicitud a través del sistema de agentes
- `GET /api/v1/agents`: Lista todos los agentes disponibles
- `GET /api/v1/health`: Verifica el estado del sistema de agentes
- `GET /metrics`: Endpoint para Prometheus (métricas)

## Despliegue con Docker

```bash
# Construir la imagen
docker build -t multi-agent-system .

# Ejecutar el contenedor
docker run -p 8000:8000 --env-file .env multi-agent-system
```

O usando Docker Compose:

```bash
docker-compose up -d
```

## Desarrolladores

Para contribuir al proyecto:

1. Ejecutar tests:
   ```bash
   pytest
   ```

2. Formatear código:
   ```bash
   black app tests
   ```

3. Verificar estilo:
   ```bash
   ruff check app tests
   ```

## Licencia

Este proyecto está licenciado bajo la licencia MIT.
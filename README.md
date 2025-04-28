# 🧠 Sistema Multi-Agente MCP con LangGraph y FastAPI

Este proyecto implementa un sistema de agentes inteligentes basados en **LangGraph** y **MCP (Model Context Protocol)**, orquestados mediante un **grafo dinámico de agentes** en un servidor **FastAPI** con instrumentación avanzada, CI/CD automatizado y arquitectura limpia y escalable. Para una prueba técnica con Sesame HR.

## 🚀 Tecnologías principales

- [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) (ASGI server)
- [LangGraph](https://langgraph.readthedocs.io/en/latest/) (Multi-agent orchestration framework)
- [LangChain](https://www.langchain.dev/) (Base LLM agents)
- **MCP Protocol** (Integración de herramientas externas estandarizada)
- **Python 3.12+**
- **Docker** (despliegue de contenedores)
- **GitHub Actions** (CI/CD)
- Observabilidad con:
  - **Sentry** (errores y performance)
  - **Grafana Loki** (centralización de logs estructurados)
  - **Prometheus** (métricas opcionales)
- **Ruff** (Linter y formateador rápido)
- **Black** (Formateador de código)
- **Pytest** (tests unitarios y de integración)

---

## 🛠️ Arquitectura

- **Servidor HTTP** FastAPI expone endpoints REST para recibir solicitudes.
- **Sistema de agentes LangGraph** orquesta múltiples agentes IA mediante un grafo dirigido dinámico.
- **Router inteligente** analiza el estado y decide dinámicamente el siguiente agente a ejecutar.
- **Herramientas externas** se consumen a través de servidores MCP mediante JSON-RPC estandarizado.
- **Logging estructurado y coloreado**, con logs persistentes y centralizados.
- **Instrumentación de tokens** y métricas de uso para control de costes y performance.
- **Arquitectura Hexagonal / Clean Architecture** que facilita escalabilidad y testabilidad.

### Diagrama general:

```
Cliente HTTP
    ↓
FastAPI (entrada HTTP)
    ↓
Router (orquestador dinámico)
   ↙       ↘
Agente A    Agente B
   ↓           ↓
Herramienta MCP  Herramienta MCP
    ↘         ↙
  Sentry / Loki / Metrics
```

---

## 📦 Instalación y despliegue local

> [TODO]: **Nota**: Para la instalación, ejecución local, testing y despliegue, consulta la guía completa en [docs/INSTALLATION.md](docs/INSTALLATION.md).

Resumen rápido:

```bash
# Clonar repositorio
git clone https://github.com/tu_usuario/tu_proyecto.git
cd tu_proyecto

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # o .venv\Scripts\activate en Windows

# Instalar dependencias
pip install -r requirements.txt

# Crear archivo .env y configurar variables (ver ejemplo en .env.example)

# Ejecutar servidor local en modo desarrollo
uvicorn app.main:app --reload
```

Para levantar el servicio en **Docker**:

```bash
# Build de la imagen
docker build -t multi-agent-ia .

# Correr el contenedor
docker run --env-file .env -p 8000:8000 multi-agent-ia
```

---

## 🧪 Testing

Para ejecutar todos los tests unitarios y de integración:

```bash
pytest
```

Cobertura de código:

```bash
pytest --cov=app --cov-report=term-missing
```

---

## 🔥 CI/CD y workflows automáticos

- **Push en develop**:
  - Linting (Ruff)
  - Formateo (Black)
  - Tests (Pytest)
  - Build de imagen Docker
  - Deploy automático a entorno de testing

- **Merge a master**:
  - Linting + Tests
  - Build imagen Docker final
  - Deploy automático a entorno de producción

Protecciones de ramas configuradas para asegurar calidad en PRs.

---

## 📈 Observabilidad y seguimiento

- **Sentry**: Captura automática de errores y performance tracing.
- **Grafana Loki**: Logs JSON centralizados, coloreados y estructurados.
- **Prometheus** (opcional): Exposición de métricas para latencia, errores, uso de tokens.
- **Tracking de tokens y coste**: Análisis de uso de OpenAI API por conversación.

---

## 🧠 Agentes inteligentes

Sistema de agentes basado en LangGraph:
- **Agente Router**: Decide dinámicamente el flujo.
- **Agentes especializados**: Ejecutan tareas concretas.
- **Memoria compartida**: Estado persistente a lo largo de la conversación.
- **Herramientas**: Usadas vía protocolos MCP, adaptables y expansibles.

---

## 📚 Estructura del repositorio

```
app/
  ├── agents/           # Definición de agentes LangGraph
  ├── core/             # Configuración de grafo LangGraph
  ├── domain/           # Entidades, casos de uso, interfaces
  ├── infra/            # Implementaciones: OpenAI, MCPClient, Logger
  ├── main.py           # FastAPI app
  └── tests/            # Unit tests, integration tests
.vscode/
  ├── launch.json       # Configuraciones de debug
  └── settings.json     # Formato, lint, entorno
.github/
  └── workflows/        # GitHub Actions CI/CD
Dockerfile
docker-compose.yml (opcional)
.env.example
requirements.txt
README.md
```

---

## 🧩 Roadmap

- Integración de nuevos agentes especializados.
- Auto-scaling de agentes según carga.
- Expansión del catálogo de herramientas MCP.
- Análisis de costes y optimización automática de prompts.

---

## 🧑‍💻 Contribución

Se aceptan contribuciones via Pull Request siguiendo las reglas de linting, testing y convenciones de arquitectura del proyecto.  
Consulta el [CONTRIBUTING.md](docs/CONTRIBUTING.md) para más detalles.

---

## 📜 Licencia

Este proyecto se entrega como código abierto bajo la Licencia [MIT](LICENSE).